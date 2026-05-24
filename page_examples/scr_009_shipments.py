"""
SCR-009 — Отгрузки и Сборка
Рабочее место кладовщика. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_009_shipments.py
"""
import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SCR-009 — Отгрузки и Сборка (демо)",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp { background: #F5F6F8 !important; }
#MainMenu, header, footer { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
div.block-container {
    max-width: 1200px !important;
    padding: 32px 32px 40px !important;
    margin: 0 auto !important;
}
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


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

TODAY = datetime.date(2026, 5, 24)

# Заказы в статусе «Сборка» — рабочий список кладовщика
ASSEMBLY_ORDERS = [
    {
        "id": 1,
        "number": "24-0117",
        "customer_name": "Магнит, ТТ Авиаторов",
        "customer_address": "г. Красноярск, ул. Авиаторов, 25",
        "delivery_date": datetime.date(2026, 5, 25),
        "courier": "Сидоров А.П.",
        "comment": "Звонить за час до доставки",
        "items": [
            {
                "product": "Сахар фасованный 0.5кг",
                "quantity": 480,
                "units_per_box": 12,
                "reservations": [
                    {"batch": "П-2026-001", "qty": 480, "expiry": "2026-12-31"},
                ],
            },
            {
                "product": "Сахар фасованный 1кг",
                "quantity": 240,
                "units_per_box": 12,
                "reservations": [
                    {"batch": "П-2026-003", "qty": 200, "expiry": "2026-12-31"},
                    {"batch": "П-2026-007", "qty": 40, "expiry": "2027-03-15"},
                ],
            },
            {
                "product": "Мука пшеничная 1кг",
                "quantity": 120,
                "units_per_box": 10,
                "reservations": [
                    {"batch": "П-2026-005", "qty": 120, "expiry": "2027-01-20"},
                ],
            },
        ],
    },
    {
        "id": 5,
        "number": "24-0121",
        "customer_name": "Лента, ТТ Взлётка",
        "customer_address": "г. Красноярск, ул. Молокова, 54",
        "delivery_date": datetime.date(2026, 5, 25),
        "courier": "Козлов Д.В.",
        "comment": "",
        "items": [
            {
                "product": "Сахар фасованный 0.5кг",
                "quantity": 720,
                "units_per_box": 12,
                "reservations": [
                    {"batch": "П-2026-002", "qty": 720, "expiry": "2026-12-31"},
                ],
            },
            {
                "product": "Мука пшеничная 1кг",
                "quantity": 600,
                "units_per_box": 10,
                "reservations": [
                    {"batch": "П-2026-005", "qty": 400, "expiry": "2027-01-20"},
                    {"batch": "П-2026-008", "qty": 200, "expiry": "2027-04-10"},
                ],
            },
        ],
    },
    {
        "id": 10,
        "number": "24-0130",
        "customer_name": "ИП Соколова О.В.",
        "customer_address": "г. Красноярск, ул. Маерчака, 12",
        "delivery_date": datetime.date(2026, 5, 26),
        "courier": "Сидоров А.П.",
        "comment": "Только после 14:00",
        "items": [
            {
                "product": "Сахар фасованный 0.5кг",
                "quantity": 126,
                "units_per_box": 12,
                "reservations": [
                    {"batch": "П-2026-004", "qty": 126, "expiry": "2026-11-15"},
                ],
            },
        ],
    },
    {
        "id": 12,
        "number": "24-0132",
        "customer_name": "Пятёрочка, ТТ Семафорная",
        "customer_address": "г. Красноярск, ул. Семафорная, 189",
        "delivery_date": datetime.date(2026, 5, 27),
        "courier": None,
        "comment": "",
        "items": [
            {
                "product": "Сахар фасованный 0.5кг",
                "quantity": 360,
                "units_per_box": 12,
                "reservations": [
                    {"batch": "П-2026-006", "qty": 360, "expiry": "2026-12-31"},
                ],
            },
            {
                "product": "Сахар фасованный 1кг",
                "quantity": 180,
                "units_per_box": 12,
                "reservations": [
                    {"batch": "П-2026-009", "qty": 180, "expiry": "2027-02-28"},
                ],
            },
            {
                "product": "Мука пшеничная 1кг",
                "quantity": 200,
                "units_per_box": 10,
                "reservations": [
                    {"batch": "П-2026-010", "qty": 200, "expiry": "2027-05-01"},
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _qty_label(qty: int, units_per_box: int) -> str:
    boxes = qty // units_per_box
    loose = qty % units_per_box
    if loose:
        return f"{boxes} кор. + {loose} шт ({qty} шт)"
    return f"{boxes} кор. ({qty} шт)"


def _readiness(order: dict) -> str:
    """Проверка: все позиции полностью зарезервированы?"""
    for item in order["items"]:
        reserved = sum(r["qty"] for r in item["reservations"])
        if reserved < item["quantity"]:
            return "⚠️ Не полностью"
    return "✅ Готов"


def _days_until(d: datetime.date) -> str:
    delta = (d - TODAY).days
    if delta == 0:
        return "сегодня"
    if delta == 1:
        return "завтра"
    if delta < 0:
        return f"просрочен на {abs(delta)} дн."
    return f"через {delta} дн."


def _to_df(orders: list[dict]) -> pd.DataFrame:
    rows = []
    for o in orders:
        total_items = sum(it["quantity"] for it in o["items"])
        total_reserved = sum(
            sum(r["qty"] for r in it["reservations"])
            for it in o["items"]
        )
        rows.append({
            "№ заказа": o["number"],
            "Заказчик": o["customer_name"],
            "Дата доставки": o["delivery_date"].strftime("%d.%m.%Y"),
            "Срок": _days_until(o["delivery_date"]),
            "Позиций": len(o["items"]),
            "Готовность": _readiness(o),
            "Курьер": o["courier"] or "—",
        })
    return pd.DataFrame(rows)


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


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------


@st.dialog("Подтверждение выдачи")
def _confirm_issue_dialog(order: dict):
    st.markdown(f"### Заказ {order['number']}")
    st.caption(f"Заказчик: {order['customer_name']}")
    st.caption(f"Курьер: {order['courier'] or 'не назначен'}")

    st.divider()
    st.markdown("**Состав заказа:**")
    for item in order["items"]:
        reserved = sum(r["qty"] for r in item["reservations"])
        status = "✅" if reserved >= item["quantity"] else "⚠️"
        st.write(f"{status} **{item['product']}** — {_qty_label(item['quantity'], item['units_per_box'])}")

    if not order["courier"]:
        st.error("Курьер не назначен! Назначьте курьера в заказе перед выдачей.")
        return

    # Проверка полноты резервов
    all_reserved = all(
        sum(r["qty"] for r in it["reservations"]) >= it["quantity"]
        for it in order["items"]
    )
    if not all_reserved:
        st.warning("Не все позиции полностью зарезервированы!")

    st.divider()
    if st.button("Выдано — передать курьеру", type="primary", use_container_width=True):
        st.success(f"Заказ {order['number']} выдан курьеру {order['courier']} (демо)")
        st.balloons()


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown("## Отгрузки и сборка")
st.caption("Рабочее место кладовщика — заказы в статусе «Сборка»")


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

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
filtered = ASSEMBLY_ORDERS.copy()
if date_filter == "Сегодня":
    filtered = [o for o in filtered if o["delivery_date"] == TODAY]
elif date_filter == "Завтра":
    filtered = [o for o in filtered if o["delivery_date"] == TODAY + datetime.timedelta(days=1)]
elif date_filter == "Эта неделя":
    week_end = TODAY + datetime.timedelta(days=(6 - TODAY.weekday()))
    filtered = [o for o in filtered if o["delivery_date"] <= week_end]

if readiness_filter == "Готов к выдаче":
    filtered = [o for o in filtered if _readiness(o) == "✅ Готов"]
elif readiness_filter == "Не полностью":
    filtered = [o for o in filtered if _readiness(o) != "✅ Готов"]


# ---------------------------------------------------------------------------
# Table + Drawer
# ---------------------------------------------------------------------------

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

            # ---- Header ----
            st.markdown(f"### Заказ {order['number']}")
            st.caption(
                f"🟡 Сборка  ·  "
                f"Доставка {order['delivery_date'].strftime('%d.%m.%Y')} ({_days_until(order['delivery_date'])})"
            )

            # ---- Action: Выдано ----
            readiness = _readiness(order)
            if readiness == "✅ Готов":
                if st.button("📦 Выдано — передать курьеру", type="primary", use_container_width=True, key="dr_issue"):
                    _confirm_issue_dialog(order)
            else:
                st.button("📦 Выдано — передать курьеру", type="primary", use_container_width=True, key="dr_issue_disabled", disabled=True)
                st.caption("⚠️ Не все позиции зарезервированы")

            st.divider()

            # ---- Section: Заказчик ----
            st.markdown("**ЗАКАЗЧИК**")
            _drawer_fields({
                "Наименование": order["customer_name"],
                "Адрес": order["customer_address"],
            })
            if order["comment"]:
                _drawer_fields({"Комментарий": order["comment"]})

            st.divider()

            # ---- Section: Курьер ----
            st.markdown("**ДОСТАВКА**")
            _drawer_fields({
                "Курьер": order["courier"] or "⚠️ не назначен",
                "Дата доставки": order["delivery_date"].strftime("%d.%m.%Y"),
            })

            st.divider()

            # ---- Section: Чек-лист сборки ----
            st.markdown("**ЧЕК-ЛИСТ СБОРКИ**")

            for i, item in enumerate(order["items"]):
                reserved = sum(r["qty"] for r in item["reservations"])
                is_covered = reserved >= item["quantity"]
                check_key = f"check_{order['id']}_{i}"

                with st.container(border=True):
                    ch1, ch2 = st.columns([1, 20])
                    checked = ch1.checkbox(
                        "ok", key=check_key, label_visibility="collapsed",
                    )
                    status_icon = "✅" if checked else ("🟢" if is_covered else "⚠️")

                    ch2.markdown(
                        f"{status_icon} **{item['product']}** — "
                        f"{_qty_label(item['quantity'], item['units_per_box'])}"
                    )

                    # Партии
                    for r in item["reservations"]:
                        ch2.caption(
                            f"└ Партия {r['batch']} · {r['qty']} шт · годен до {r['expiry']}"
                        )

                    if not is_covered:
                        deficit = item["quantity"] - reserved
                        ch2.caption(f"└ ❌ Не хватает: {deficit} шт")

            # Итог чек-листа
            total_items = len(order["items"])
            checked_count = sum(
                1 for i in range(total_items)
                if st.session_state.get(f"check_{order['id']}_{i}", False)
            )
            if checked_count == total_items:
                st.success(f"Все {total_items} позиций собраны!")
            else:
                st.caption(f"Собрано: {checked_count} из {total_items} позиций")
else:
    _table(df, key="tbl_shipments")


# ---------------------------------------------------------------------------
# Summary bar
# ---------------------------------------------------------------------------

total = len(ASSEMBLY_ORDERS)
ready_count = sum(1 for o in ASSEMBLY_ORDERS if _readiness(o) == "✅ Готов")
today_count = sum(1 for o in ASSEMBLY_ORDERS if o["delivery_date"] == TODAY)
tomorrow_count = sum(1 for o in ASSEMBLY_ORDERS if o["delivery_date"] == TODAY + datetime.timedelta(days=1))

parts = [f"На сборке: **{total}** заказов"]
if ready_count:
    parts.append(f"✅ Готовы: **{ready_count}**")
if today_count:
    parts.append(f"📅 Сегодня: **{today_count}**")
if tomorrow_count:
    parts.append(f"📅 Завтра: **{tomorrow_count}**")

st.caption("   ·   ".join(parts))
