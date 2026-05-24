"""SCR-009 — Отгрузки и Сборка. Рабочее место кладовщика."""

import datetime

import pandas as pd
import streamlit as st

from api_client import APIError, get_client

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles

TODAY = datetime.date.today()


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
div[data-testid="stTextInputRootElement"] input {
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    height: 34px !important;
    font-size: 13px !important;
}
div[data-testid="stSelectboxRootElement"] > div {
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
button[data-testid="stBaseButton-primary"] {
    background-color: #1E293B !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    height: 38px !important;
}
button[data-testid="stBaseButton-secondary"] {
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    height: 38px !important;
}
</style>
""", unsafe_allow_html=True)


# ── Load reference data ───────────────────────────────────────────────────────

try:
    users = client.get("/users")
    delivery_users = [u for u in users if "delivery" in u.get("roles", [])]
    delivery_user_map = {u["id"]: u["full_name"] for u in delivery_users}
except APIError as e:
    _err(e)
    delivery_user_map = {}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _order_number_label(number: int) -> str:
    year = TODAY.year % 100
    return f"{year}-{number:04d}"


def _qty_label(qty: int, units_per_box: int) -> str:
    if units_per_box <= 1:
        return f"{qty} шт"
    boxes = qty // units_per_box
    loose = qty % units_per_box
    if loose:
        return f"{boxes} кор. + {loose} шт ({qty} шт)"
    return f"{boxes} кор. ({qty} шт)"


def _days_until(d_str: str) -> str:
    d = datetime.date.fromisoformat(d_str)
    delta = (d - TODAY).days
    if delta == 0:
        return "сегодня"
    if delta == 1:
        return "завтра"
    if delta < 0:
        return f"просрочен на {abs(delta)} дн."
    return f"через {delta} дн."


def _readiness(items: list[dict], res_by_item: dict) -> str:
    for item in items:
        pid_key = str(item["product_id"])
        reserved = sum(r["quantity"] for r in res_by_item.get(pid_key, []))
        if reserved < item["quantity"]:
            return "⚠️ Не полностью"
    return "✅ Готов"


def _table(df: pd.DataFrame, key: str):
    return st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )


def _selected_rows(key: str) -> list[int]:
    return st.session_state.get(key, {}).get("selection", {}).get("rows", [])


def _drawer_fields(fields: dict):
    for k, v in fields.items():
        col_k, col_v = st.columns([2, 3])
        col_k.caption(k)
        col_v.markdown(f"**{v}**")


# ── Load orders in assembly status ────────────────────────────────────────────

try:
    orders = client.get("/orders", status="assembly")
except APIError as e:
    _err(e)
    orders = []

# Pre-load drawer data for all orders to compute readiness
drawer_cache: dict[int, dict] = {}
for o in orders:
    try:
        drawer_cache[o["id"]] = client.get(f"/orders/{o['id']}/drawer")
    except APIError:
        drawer_cache[o["id"]] = None


def _to_df(order_list: list[dict]) -> pd.DataFrame:
    rows = []
    for o in order_list:
        d = drawer_cache.get(o["id"])
        items = d["items"] if d else []
        res_by_item = d["reservations_by_item"] if d else {}
        total_items = len(items)

        rows.append({
            "№ заказа": _order_number_label(o["number"]),
            "Заказчик": o["customer_name"],
            "Дата доставки": o["delivery_date"],
            "Срок": _days_until(o["delivery_date"]),
            "Позиций": total_items,
            "Готовность": _readiness(items, res_by_item),
            "Курьер": o.get("delivery_user_name") or "—",
        })
    return pd.DataFrame(rows)


# ── Dialog: Подтверждение выдачи ──────────────────────────────────────────────


@st.dialog("Отгрузка — передать курьеру")
def _confirm_issue_dialog(order: dict, drawer: dict):
    o = drawer["order"]
    items = drawer["items"]

    st.markdown(f"### Заказ {_order_number_label(o['number'])}")
    st.caption(f"Заказчик: {o['customer_name']}")
    st.caption(f"Курьер: {o.get('delivery_user_name') or 'не назначен'}")

    st.divider()
    st.markdown("**Состав заказа:**")
    res_by_item = drawer["reservations_by_item"]
    for item in items:
        pid_key = str(item["product_id"])
        reserved = sum(r["quantity"] for r in res_by_item.get(pid_key, []))
        status_icon = "✅" if reserved >= item["quantity"] else "⚠️"
        upb = item.get("units_per_box", 1)
        st.write(f"{status_icon} **{item['product_name']}** — {_qty_label(item['quantity'], upb)}")

    if not o.get("delivery_user_id"):
        st.error("Курьер не назначен! Назначьте курьера в заказе перед отгрузкой.")
        return

    st.divider()

    driver_ids = list(delivery_user_map.keys())
    if not driver_ids:
        st.warning("Нет доступных курьеров с ролью «Доставка».")
        return

    default_idx = 0
    if o.get("delivery_user_id") and o["delivery_user_id"] in driver_ids:
        default_idx = driver_ids.index(o["delivery_user_id"])

    executor_id = st.selectbox(
        "Курьер",
        options=driver_ids,
        index=default_idx,
        format_func=lambda x: delivery_user_map[x],
    )
    planned_date = st.date_input(
        "Плановая дата доставки",
        value=datetime.date.fromisoformat(o["delivery_date"])
        if o.get("delivery_date")
        else TODAY,
    )

    if st.button("Создать доставку и выдать", type="primary", use_container_width=True):
        try:
            client.post("/deliveries", body={
                "order_id": o["id"],
                "executor_id": executor_id,
                "planned_date": str(planned_date),
            })
            client.patch(
                f"/orders/{o['id']}/status",
                body={"new_status": "delivery"},
            )
            st.rerun()
        except APIError as e:
            _err(e)


# ── Page header ───────────────────────────────────────────────────────────────

st.title("Отгрузки и сборка")
st.caption("Рабочее место кладовщика — заказы в статусе «Сборка»")


# ── Filters ───────────────────────────────────────────────────────────────────

c1, c2 = st.columns([1, 1])
date_filter = c1.selectbox(
    "Период",
    options=["Все", "Сегодня", "Завтра", "Эта неделя"],
    label_visibility="collapsed",
    key="filter_date",
)
readiness_filter = c2.selectbox(
    "Готовность",
    options=["Все", "Готов к выдаче", "Не полностью"],
    label_visibility="collapsed",
    key="filter_readiness",
)

# Apply filters
filtered = orders.copy()
if date_filter == "Сегодня":
    filtered = [o for o in filtered if o["delivery_date"] == str(TODAY)]
elif date_filter == "Завтра":
    tomorrow = str(TODAY + datetime.timedelta(days=1))
    filtered = [o for o in filtered if o["delivery_date"] == tomorrow]
elif date_filter == "Эта неделя":
    week_end = TODAY + datetime.timedelta(days=(6 - TODAY.weekday()))
    filtered = [o for o in filtered if o["delivery_date"] <= str(week_end)]

if readiness_filter != "Все":
    for o in filtered[:]:
        d = drawer_cache.get(o["id"])
        if not d:
            filtered.remove(o)
            continue
        r = _readiness(d["items"], d["reservations_by_item"])
        if readiness_filter == "Готов к выдаче" and r != "✅ Готов":
            filtered.remove(o)
        elif readiness_filter == "Не полностью" and r == "✅ Готов":
            filtered.remove(o)


# ── Table + Drawer ────────────────────────────────────────────────────────────

df = _to_df(filtered)

if df.empty:
    st.info("Нет заказов на сборку по выбранным фильтрам.")
elif _selected_rows("tbl_shipments"):
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_shipments")
    with col_dr:
        rows = sel.selection.rows
        if rows and rows[0] < len(filtered):
            order = filtered[rows[0]]
            drawer = drawer_cache.get(order["id"])

            if drawer:
                o = drawer["order"]
                items = drawer["items"]
                res_by_item = drawer["reservations_by_item"]

                # ---- Header ----
                st.markdown(f"### Заказ {_order_number_label(o['number'])}")
                st.caption(
                    f"🟡 Сборка  ·  "
                    f"Доставка {o['delivery_date']} ({_days_until(o['delivery_date'])})"
                )

                # ---- Action: Выдано ----
                readiness = _readiness(items, res_by_item)
                if readiness == "✅ Готов":
                    if st.button(
                        "📦 Выдано — передать курьеру",
                        type="primary",
                        use_container_width=True,
                        key="dr_issue",
                    ):
                        _confirm_issue_dialog(order, drawer)
                else:
                    st.button(
                        "📦 Выдано — передать курьеру",
                        type="primary",
                        use_container_width=True,
                        key="dr_issue_disabled",
                        disabled=True,
                    )
                    st.caption("⚠️ Не все позиции зарезервированы")

                st.divider()

                # ---- Section: Заказчик ----
                st.markdown("**ЗАКАЗЧИК**")
                _drawer_fields({
                    "Наименование": o["customer_name"],
                    "Адрес": o["delivery_address"],
                })
                if o.get("comment"):
                    _drawer_fields({"Комментарий": o["comment"]})

                st.divider()

                # ---- Section: Доставка ----
                st.markdown("**ДОСТАВКА**")
                _drawer_fields({
                    "Курьер": o.get("delivery_user_name") or "⚠️ не назначен",
                    "Дата доставки": o["delivery_date"],
                })

                st.divider()

                # ---- Section: Чек-лист сборки ----
                st.markdown("**ЧЕК-ЛИСТ СБОРКИ**")

                for i, item in enumerate(items):
                    pid_key = str(item["product_id"])
                    item_reservations = res_by_item.get(pid_key, [])
                    reserved = sum(r["quantity"] for r in item_reservations)
                    is_covered = reserved >= item["quantity"]
                    upb = item.get("units_per_box", 1)
                    check_key = f"check_{o['id']}_{i}"

                    with st.container(border=True):
                        ch1, ch2 = st.columns([1, 20])
                        checked = ch1.checkbox(
                            "ok", key=check_key, label_visibility="collapsed",
                        )
                        status_icon = "✅" if checked else ("🟢" if is_covered else "⚠️")

                        ch2.markdown(
                            f"{status_icon} **{item['product_name']}** — "
                            f"{_qty_label(item['quantity'], upb)}"
                        )

                        for r in item_reservations:
                            ch2.caption(
                                f"└ {r['batch_label']} · {r['quantity']} шт зарезервировано"
                            )

                        if not is_covered:
                            deficit = item["quantity"] - reserved
                            ch2.caption(f"└ ❌ Не хватает: {deficit} шт")

                # Итог чек-листа
                total_items = len(items)
                checked_count = sum(
                    1 for i in range(total_items)
                    if st.session_state.get(f"check_{o['id']}_{i}", False)
                )
                if checked_count == total_items:
                    st.success(f"Все {total_items} позиций собраны!")
                else:
                    st.caption(f"Собрано: {checked_count} из {total_items} позиций")
else:
    _table(df, key="tbl_shipments")


# ── Summary bar ───────────────────────────────────────────────────────────────

total = len(orders)
ready_count = 0
today_count = 0
tomorrow_count = 0
tomorrow_str = str(TODAY + datetime.timedelta(days=1))

for o in orders:
    d = drawer_cache.get(o["id"])
    if d and _readiness(d["items"], d["reservations_by_item"]) == "✅ Готов":
        ready_count += 1
    if o["delivery_date"] == str(TODAY):
        today_count += 1
    if o["delivery_date"] == tomorrow_str:
        tomorrow_count += 1

parts = [f"На сборке: **{total}** заказов"]
if ready_count:
    parts.append(f"✅ Готовы: **{ready_count}**")
if today_count:
    parts.append(f"📅 Сегодня: **{today_count}**")
if tomorrow_count:
    parts.append(f"📅 Завтра: **{tomorrow_count}**")

st.caption("   ·   ".join(parts))
