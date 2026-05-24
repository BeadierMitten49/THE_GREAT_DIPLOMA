import datetime

import pandas as pd
import streamlit as st

from api_client import APIError, get_client

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles

STATUS_OPTIONS = ["", "created", "production", "assembly", "delivery", "completed"]
STATUS_LABELS = {
    "": "Все",
    "created": "Создан",
    "production": "Производство",
    "assembly": "Сборка",
    "delivery": "Доставка",
    "completed": "Завершён",
}
STATUS_EMOJI = {
    "created": "⚪",
    "production": "🔵",
    "assembly": "🟡",
    "delivery": "🟢",
    "completed": "✅",
}

ALLOWED_TRANSITIONS = {
    "created": ["production", "assembly"],
    "production": ["assembly"],
    "assembly": ["delivery"],
    "delivery": ["completed"],
}


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
    customers = client.get("/references/customers", include_inactive=False)
    customer_list = {c["id"]: c for c in customers}
    products = client.get("/references/products", include_inactive=False)
    product_map = {p["id"]: p["name"] for p in products}
    users = client.get("/users")
    delivery_users = [u for u in users if "delivery" in u.get("roles", [])]
    delivery_user_map = {u["id"]: u["full_name"] for u in delivery_users}
    production_users = [u for u in users if "production" in u.get("roles", [])]
    production_user_map = {u["id"]: u["full_name"] for u in production_users}
except APIError as e:
    _err(e)
    customer_list = {}
    product_map = {}
    delivery_user_map = {}
    production_user_map = {}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _order_number_label(number: int) -> str:
    year = datetime.date.today().year % 100
    return f"{year}-{number:04d}"


def _status_label(status: str) -> str:
    return f"{STATUS_EMOJI.get(status, '')} {STATUS_LABELS.get(status, status)}"


def _item_qty_label(item: dict) -> str:
    upb = item.get("units_per_box", 1)
    qty = item["quantity"]
    if upb > 1:
        boxes = qty // upb
        loose = qty % upb
        if loose:
            return f"{boxes} кор. / {loose} шт"
        return f"{boxes} кор."
    return f"{qty} шт"


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


def _to_df(orders: list[dict]) -> pd.DataFrame:
    rows = []
    for o in orders:
        rows.append({
            "№": _order_number_label(o["number"]),
            "Заказчик": o["customer_name"],
            "Дата доставки": o["delivery_date"],
            "Статус": _status_label(o["status"]),
        })
    return pd.DataFrame(rows)


# ── Dialogs ───────────────────────────────────────────────────────────────────


@st.dialog("Создать заказ")
def _create_order_dialog():
    cust_ids = list(customer_list.keys())
    if not cust_ids:
        st.warning("Нет клиентов в справочнике.")
        return
    cust_id = st.selectbox(
        "Заказчик",
        options=cust_ids,
        format_func=lambda x: customer_list[x]["name"],
    )
    cust = customer_list.get(cust_id, {})
    address = st.text_input("Адрес доставки", value=cust.get("default_address", ""))
    delivery_date = st.date_input(
        "Дата доставки",
        value=datetime.date.today() + datetime.timedelta(days=3),
    )
    comment = st.text_input("Комментарий", value="")

    driver_options = [None] + list(delivery_user_map.keys())
    driver_id = st.selectbox(
        "Водитель",
        options=driver_options,
        format_func=lambda x: delivery_user_map.get(x, "— не назначен —") if x else "— не назначен —",
    )

    st.divider()
    st.markdown("**Позиции заказа**")
    prod_ids = list(product_map.keys())
    if not prod_ids:
        st.warning("Нет продуктов в справочнике.")
        return
    n_items = st.number_input("Количество позиций", min_value=1, max_value=50, value=1)
    items = []
    for i in range(int(n_items)):
        c1, c2 = st.columns(2)
        pid = c1.selectbox(
            "Товар", options=prod_ids,
            format_func=lambda x: product_map.get(x, str(x)),
            key=f"new_order_prod_{i}",
        )
        qty = c2.number_input("Кол-во (шт)", min_value=1, value=1, key=f"new_order_qty_{i}")
        items.append({"product_id": pid, "quantity": qty})

    if st.button("Создать", type="primary", use_container_width=True):
        try:
            client.post("/orders", body={
                "customer_id": cust_id,
                "delivery_address": address,
                "delivery_date": str(delivery_date),
                "items": items,
                "delivery_user_id": driver_id,
                "comment": comment if comment else None,
            })
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Редактировать заказ")
def _edit_order_dialog(order: dict, order_items: list[dict]):
    address = st.text_input("Адрес доставки", value=order["delivery_address"])
    delivery_date = st.date_input(
        "Дата доставки",
        value=datetime.date.fromisoformat(order["delivery_date"]),
    )
    comment = st.text_input("Комментарий", value=order.get("comment") or "")

    driver_options = [None] + list(delivery_user_map.keys())
    driver_id = st.selectbox(
        "Водитель",
        options=driver_options,
        format_func=lambda x: delivery_user_map.get(x, "— не назначен —") if x else "— не назначен —",
        index=(
            driver_options.index(order["delivery_user_id"])
            if order.get("delivery_user_id") in driver_options
            else 0
        ),
    )

    st.divider()
    st.markdown("**Позиции заказа**")
    prod_ids = list(product_map.keys())
    n_items = st.number_input(
        "Количество позиций", min_value=1, max_value=50,
        value=max(len(order_items), 1),
    )
    items = []
    for i in range(int(n_items)):
        c1, c2 = st.columns(2)
        existing = order_items[i] if i < len(order_items) else None
        pid = c1.selectbox(
            "Товар", options=prod_ids,
            format_func=lambda x: product_map.get(x, str(x)),
            index=prod_ids.index(existing["product_id"]) if existing and existing["product_id"] in prod_ids else 0,
            key=f"edit_order_prod_{i}",
        )
        qty = c2.number_input(
            "Кол-во (шт)", min_value=1,
            value=existing["quantity"] if existing else 1,
            key=f"edit_order_qty_{i}",
        )
        items.append({"product_id": pid, "quantity": qty})

    if st.button("Сохранить", type="primary", use_container_width=True):
        try:
            client.put(f"/orders/{order['id']}", body={
                "delivery_address": address,
                "delivery_date": str(delivery_date),
                "items": items,
                "delivery_user_id": driver_id,
                "comment": comment if comment else None,
            })
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Сменить статус")
def _change_status_dialog(order: dict):
    current = order["status"]
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    if not allowed:
        st.info(f"Из статуса «{STATUS_LABELS.get(current, current)}» нет доступных переходов.")
        return
    new_status = st.selectbox(
        "Новый статус",
        options=allowed,
        format_func=lambda x: _status_label(x),
    )
    if st.button("Применить", type="primary", use_container_width=True):
        try:
            client.patch(f"/orders/{order['id']}/status", body={"new_status": new_status})
            st.rerun()
        except APIError as e:
            _err(e)


def _reserve_form(order: dict, items: list[dict], res_by_item: dict) -> bool:
    """Render reservation form inside a dialog. Returns True if all items are fully covered."""
    st.caption(f"Заказ № {_order_number_label(order['number'])}")
    any_reserved = False
    all_covered = True

    for item in items:
        pid = item["product_id"]
        pid_key = str(pid)
        existing = res_by_item.get(pid_key, [])
        already_reserved = sum(r["quantity"] for r in existing)
        needed = item["quantity"] - already_reserved

        st.markdown(f"**{item['product_name']}** — нужно {item['quantity']} шт, зарезервировано {already_reserved} шт")

        if needed <= 0:
            st.success("Полностью зарезервировано")
            st.divider()
            continue

        all_covered = False

        try:
            stocks = client.get("/warehouse/product-stock", product_id=pid)
        except APIError as e:
            _err(e)
            stocks = []

        available_stocks = [
            s for s in stocks
            if s["quantity"] - s["reserved"] > 0
        ]

        if not available_stocks:
            st.warning("Нет доступных партий на складе")
            st.divider()
            continue

        for s in available_stocks:
            avail = s["quantity"] - s["reserved"]
            label = f"П-{s['batch_year']}-{s['batch_number']:03d}"
            sc1, sc2, sc3 = st.columns([3, 2, 1])
            sc1.caption(f"{label} · {avail} шт свободно · годен до {s['expiry_date']}")
            qty = sc2.number_input(
                "Кол-во",
                min_value=0,
                max_value=min(avail, needed),
                value=0,
                key=f"res_{order['id']}_{pid}_{s['id']}",
                label_visibility="collapsed",
            )
            if sc3.button("✓", key=f"res_btn_{order['id']}_{pid}_{s['id']}"):
                if qty > 0:
                    try:
                        client.post(
                            f"/orders/{order['id']}/reservations",
                            body={"stock_id": s["id"], "quantity": qty},
                        )
                        any_reserved = True
                    except APIError as e:
                        _err(e)

        st.divider()

    if any_reserved:
        st.rerun()

    return all_covered


@st.dialog("Зарезервировать продукцию", width="large")
def _reserve_dialog(order: dict, items: list[dict], res_by_item: dict):
    _reserve_form(order, items, res_by_item)


@st.dialog("Сборка — резервирование продукции", width="large")
def _reserve_and_set_assembly_dialog(order: dict, items: list[dict], res_by_item: dict):
    all_covered = _reserve_form(order, items, res_by_item)
    if all_covered:
        if st.button("Готово — перевести в Сборка", type="primary", use_container_width=True):
            try:
                client.patch(f"/orders/{order['id']}/status", body={"new_status": "assembly"})
                st.rerun()
            except APIError as e:
                _err(e)
    else:
        st.info("Зарезервируйте все позиции, чтобы перевести заказ в Сборка.")


@st.dialog("Снять резервы")
def _release_reservations_dialog(order: dict):
    st.warning(
        f"Снять все резервы с заказа "
        f"**№ {_order_number_label(order['number'])}**?"
    )
    if st.button("Снять все", type="primary", use_container_width=True):
        try:
            client.delete(f"/orders/{order['id']}/reservations")
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Производство — создать задачу")
def _create_task_and_set_production_dialog(order: dict, items: list[dict]):
    st.caption(f"Заказ № {_order_number_label(order['number'])}")
    st.markdown("Будет создана производственная задача для позиций заказа:")
    for item in items:
        st.write(f"- **{item['product_name']}** — {_item_qty_label(item)}")

    st.divider()

    prod_ids = list(production_user_map.keys())
    if not prod_ids:
        st.warning("Нет доступных исполнителей с ролью «Производство».")
        return

    executor_id = st.selectbox(
        "Исполнитель",
        options=prod_ids,
        format_func=lambda x: production_user_map[x],
    )
    dc1, dc2 = st.columns(2)
    start_date = dc1.date_input("Дата начала", value=datetime.date.today())
    deadline = dc2.date_input(
        "Дедлайн",
        value=datetime.date.fromisoformat(order["delivery_date"])
        if order.get("delivery_date")
        else datetime.date.today() + datetime.timedelta(days=3),
    )
    comment = st.text_input("Комментарий", value="")

    if st.button("Создать задачу и перевести в Производство", type="primary", use_container_width=True):
        try:
            for item in items:
                client.post("/tasks", body={
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "executor_id": executor_id,
                    "start_date": str(start_date),
                    "deadline": str(deadline),
                    "task_type": "order_task",
                    "order_id": order["id"],
                    "comment": comment if comment else None,
                })
            client.patch(f"/orders/{order['id']}/status", body={"new_status": "production"})
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Доставка — создать и отправить", width="large")
def _create_delivery_and_set_status_dialog(order: dict, items: list[dict]):
    st.caption(f"Заказ № {_order_number_label(order['number'])}")
    st.markdown(
        "Создайте доставку для заказа. После создания заказ будет "
        "переведён в статус **Доставка**."
    )

    # ---- Чек-лист сборки ----
    st.divider()
    st.markdown("**Чек-лист сборки**")
    all_checked = True
    for i, item in enumerate(items):
        checked = st.checkbox(
            f"{item['product_name']} — {_item_qty_label(item)}",
            value=item.get("is_assembled", False),
            key=f"dlg_check_{order['id']}_{item['id']}",
        )
        if not item.get("is_assembled", False) and checked:
            try:
                client.patch(f"/orders/items/{item['id']}/assembled", body={"is_assembled": True})
            except APIError as e:
                _err(e)
        elif item.get("is_assembled", False) and not checked:
            try:
                client.patch(f"/orders/items/{item['id']}/assembled", body={"is_assembled": False})
            except APIError as e:
                _err(e)
        if not checked:
            all_checked = False

    if not all_checked:
        st.info("Отметьте все позиции как собранные для создания доставки.")
        return

    st.success("Все позиции собраны!")
    st.divider()

    driver_ids = list(delivery_user_map.keys())
    if not driver_ids:
        st.warning("Нет доступных курьеров с ролью «Доставка».")
        return

    # pre-select driver already assigned to order if any
    default_idx = 0
    if order.get("delivery_user_id") and order["delivery_user_id"] in driver_ids:
        default_idx = driver_ids.index(order["delivery_user_id"])

    executor_id = st.selectbox(
        "Курьер",
        options=driver_ids,
        index=default_idx,
        format_func=lambda x: delivery_user_map[x],
    )
    planned_date = st.date_input(
        "Плановая дата доставки",
        value=datetime.date.fromisoformat(order["delivery_date"])
        if order.get("delivery_date")
        else datetime.date.today(),
    )

    if st.button(
        "Создать доставку и перевести в Доставка",
        type="primary",
        use_container_width=True,
    ):
        try:
            client.post("/deliveries", body={
                "order_id": order["id"],
                "executor_id": executor_id,
                "planned_date": str(planned_date),
            })
            client.patch(
                f"/orders/{order['id']}/status",
                body={"new_status": "delivery"},
            )
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Удалить заказ")
def _delete_order_dialog(order: dict):
    st.warning(
        f"Вы уверены, что хотите удалить заказ "
        f"**№ {_order_number_label(order['number'])}** — {order['customer_name']}?"
    )
    if st.button("Удалить", type="primary", use_container_width=True):
        try:
            client.delete(f"/orders/{order['id']}")
            st.rerun()
        except APIError as e:
            _err(e)


# ── Page header ───────────────────────────────────────────────────────────────

st.title("Заказы")

h1, h2 = st.columns([4, 1])
if is_director:
    if h2.button("+ Создать заказ", type="primary", use_container_width=True):
        _create_order_dialog()


# ── Filters ───────────────────────────────────────────────────────────────────

c1, c2, c3 = st.columns([1, 1, 1])
status_filter = c1.selectbox(
    "Статус", options=STATUS_OPTIONS,
    format_func=lambda x: STATUS_LABELS.get(x, x),
    label_visibility="collapsed", key="filter_status",
)
date_from = c2.date_input(
    "Доставка от", value=None,
    format="DD.MM.YYYY", label_visibility="collapsed",
    key="filter_date_from",
)
date_to = c3.date_input(
    "Доставка до", value=None,
    format="DD.MM.YYYY", label_visibility="collapsed",
    key="filter_date_to",
)


# ── Load orders ───────────────────────────────────────────────────────────────

try:
    orders = client.get(
        "/orders",
        status=status_filter if status_filter else None,
        delivery_date_from=str(date_from) if date_from else None,
        delivery_date_to=str(date_to) if date_to else None,
    )
except APIError as e:
    _err(e)
    orders = []


# ── Table + Drawer ────────────────────────────────────────────────────────────

df = _to_df(orders)

sel_rows = _selected_rows("tbl_orders")
sel_order = (
    orders[sel_rows[0]]
    if sel_rows and sel_rows[0] < len(orders)
    else None
)

if df.empty:
    if status_filter or date_from or date_to:
        st.info("Нет заказов по выбранным фильтрам.")
    else:
        st.info("Заказов пока нет. Создайте первый заказ кнопкой справа сверху.")
elif sel_rows:
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_orders")
    with col_dr:
        rows = sel.selection.rows
        if rows and rows[0] < len(orders):
            order = orders[rows[0]]

            # Load drawer data
            try:
                drawer = client.get(f"/orders/{order['id']}/drawer")
            except APIError as e:
                _err(e)
                drawer = None

            if drawer:
                o = drawer["order"]
                items = drawer["items"]
                res_by_item = drawer["reservations_by_item"]
                tasks = drawer["tasks"]

                # ---- Header ----
                st.markdown(f"### Заказ {o['customer_name'].split(',')[0]}")
                st.caption(
                    f"{_status_label(o['status'])}  ·  "
                    f"Создан {o['created_at'][:10] if o.get('created_at') else '—'}  ·  "
                    f"Доставка {o['delivery_date']}"
                )

                # ---- Actions ----
                if is_director and o["status"] not in ("delivery", "completed"):
                    if o["status"] == "created":
                        ac1, ac2, ac3, ac4 = st.columns(4)
                        if ac1.button("✎ Ред.", key="dr_edit"):
                            _edit_order_dialog(o, items)
                        if ac2.button("→ Производство", key="dr_to_prod"):
                            _create_task_and_set_production_dialog(o, items)
                        if ac3.button("→ Сборка", type="primary", key="dr_to_assembly"):
                            _reserve_and_set_assembly_dialog(o, items, res_by_item)
                        if ac4.button("🗑", key="dr_delete"):
                            _delete_order_dialog(o)
                    elif o["status"] == "production":
                        all_tasks_closed = tasks and all(t["status"] == "closed" for t in tasks)
                        ac1, ac2, ac3 = st.columns(3)
                        if ac1.button("✎ Редактировать", key="dr_edit"):
                            _edit_order_dialog(o, items)
                        if all_tasks_closed:
                            if ac2.button("→ Сборка", type="primary", key="dr_to_assembly"):
                                _reserve_and_set_assembly_dialog(o, items, res_by_item)
                        else:
                            ac2.button("→ Сборка", type="primary", key="dr_to_assembly", disabled=True)
                            st.caption("Переход в сборку доступен после закрытия всех задач")
                        if ac3.button("🗑 Удалить", key="dr_delete"):
                            _delete_order_dialog(o)
                    elif o["status"] == "assembly":
                        ac1, ac2, ac3 = st.columns(3)
                        if ac1.button("✎ Редактировать", key="dr_edit"):
                            _edit_order_dialog(o, items)
                        if ac2.button("→ Доставка", type="primary", key="dr_to_delivery"):
                            _create_delivery_and_set_status_dialog(o, items)
                        if ac3.button("🗑 Удалить", key="dr_delete"):
                            _delete_order_dialog(o)

                if is_director and o["status"] == "assembly":
                    has_any_res = any(res_by_item.get(str(it["product_id"]), []) for it in items)
                    if has_any_res:
                        rc1, rc2 = st.columns(2)
                    else:
                        rc1 = st.container()
                    if rc1.button("📦 Зарезервировать", key="dr_reserve", use_container_width=True):
                        _reserve_dialog(o, items, res_by_item)
                    if has_any_res:
                        if rc2.button("✕ Снять резервы", key="dr_release", use_container_width=True):
                            _release_reservations_dialog(o)

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

                # ---- Section: Состав заказа ----
                st.markdown("**СОСТАВ ЗАКАЗА**")
                for item in items:
                    st.write(f"**{item['product_name']}** — {_item_qty_label(item)}")
                    pid_key = str(item["product_id"])
                    item_reservations = res_by_item.get(pid_key, [])
                    if item_reservations:
                        for r in item_reservations:
                            st.caption(f"└ {r['batch_label']} · {r['quantity']} шт зарезервировано")
                    elif o["status"] == "production":
                        task_for_item = next(
                            (t for t in tasks if item["product_name"].startswith(t["product_name"].split(" ")[0])),
                            None,
                        )
                        if task_for_item:
                            st.caption(f"└ ⚠ Резерв не создан — задача #{task_for_item['task_id']} {STATUS_LABELS.get(task_for_item['status'], task_for_item['status'])}")
                        else:
                            st.caption("└ ⚠ Резерв не создан")

                # ---- Section: Производственные задачи ----
                if tasks:
                    st.divider()
                    st.markdown("**ПРОИЗВОДСТВЕННЫЕ ЗАДАЧИ**")
                    for t in tasks:
                        with st.container(border=True):
                            st.write(f"**{t['product_name']}** · {t['quantity']} шт · #{t['task_id']}")
                            tc1, tc2 = st.columns([3, 1])
                            tc1.caption(f"{t['executor_name']} · до {t['deadline']}")
                            tc2.write(_status_label(t["status"]))

                st.divider()

                # ---- Section: Доставка ----
                st.markdown("**ДОСТАВКА**")
                _drawer_fields({
                    "Курьер": o.get("delivery_user_name") or "не назначен",
                    "Дата плановая": o["delivery_date"],
                })
else:
    _table(df, key="tbl_orders")


# ── Summary bar ───────────────────────────────────────────────────────────────

total = len(orders)
status_counts: dict[str, int] = {}
for o in orders:
    status_counts[o["status"]] = status_counts.get(o["status"], 0) + 1

if status_filter or date_from or date_to:
    found_str = f"Найдено: **{total}** заказов"
else:
    found_str = f"Всего заказов: **{total}**"

parts = [found_str]
for s in ["created", "production", "assembly", "delivery"]:
    cnt = status_counts.get(s, 0)
    if cnt:
        parts.append(f"{STATUS_EMOJI.get(s, '')} {STATUS_LABELS.get(s, s)}: **{cnt}**")

st.caption("   ·   ".join(parts))
