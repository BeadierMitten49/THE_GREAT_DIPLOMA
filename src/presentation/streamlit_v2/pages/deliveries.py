import streamlit as st

from api_client import APIError, get_client

st.title("Доставки")

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles

DELIVERY_STATUS_LABELS = {
    "pending": "Ожидает",
    "picked_up": "У водителя",
    "in_transit": "В пути",
    "completed": "Доставлено",
    "cancelled": "Отменена",
}

DELIVERY_STATUS_ICONS = {
    "pending": "⚪",
    "picked_up": "🔵",
    "in_transit": "🚛",
    "completed": "✅",
    "cancelled": "❌",
}


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load reference data ───────────────────────────────────────────────────────
try:
    if is_director:
        users = client.get("/users")
        delivery_users = [u for u in users if "delivery" in u.get("roles", [])]
        delivery_user_map = {u["id"]: u["full_name"] for u in delivery_users}
    else:
        me = client.get("/users/me")
        delivery_user_map = {me["id"]: me["full_name"]}
except APIError as e:
    _err(e)
    delivery_user_map = {}


# ── Filters ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1, 1, 1])

status_filter = c1.selectbox(
    "Статус",
    options=["active", "pending", "picked_up", "in_transit", "completed", "cancelled"],
    format_func=lambda x: "Все активные" if x == "active" else DELIVERY_STATUS_LABELS.get(x, x),
    key="del_filter_status",
)

courier_options = ["all"] + list(delivery_user_map.keys())
courier_filter = c2.selectbox(
    "Исполнитель",
    options=courier_options,
    format_func=lambda x: "Любой" if x == "all" else delivery_user_map.get(x, str(x)),
    key="del_filter_courier",
)

date_filter = c3.date_input("Дата", value=None, key="del_filter_date")


# ── Load deliveries ───────────────────────────────────────────────────────────
try:
    params = {}
    if status_filter != "active":
        params["status"] = status_filter
    if courier_filter != "all":
        params["executor_id"] = courier_filter
    deliveries = client.get("/deliveries", **params)
except APIError as e:
    _err(e)
    deliveries = []

# Client-side filters
if status_filter == "active":
    deliveries = [d for d in deliveries if d["status"] not in ("cancelled",)]
if date_filter:
    deliveries = [d for d in deliveries if d["planned_date"] == str(date_filter)]

# ── Load order info for display ──────────────────────────────���────────────────
order_cache: dict[int, dict] = {}


def _get_order(order_id: int) -> dict | None:
    if order_id not in order_cache:
        try:
            order_cache[order_id] = client.get(f"/orders/{order_id}")
        except APIError:
            order_cache[order_id] = None
    return order_cache[order_id]


# ── Helpers ──────────────────────────────────────────────────────────��────────


def _build_table_data(deliveries: list[dict]) -> list[dict]:
    rows = []
    for d in deliveries:
        order = _get_order(d["order_id"])
        customer = order.get("customer_name", f"Заказ #{d['order_id']}") if order else f"Заказ #{d['order_id']}"
        address = order.get("delivery_address", "—") if order else "—"
        executor_name = delivery_user_map.get(d["executor_id"], f"id={d['executor_id']}")
        icon = DELIVERY_STATUS_ICONS.get(d["status"], "")
        label = DELIVERY_STATUS_LABELS.get(d["status"], d["status"])
        rows.append({
            "Дата": d["planned_date"],
            "Заказчик": customer,
            "Адрес": address,
            "Исполнитель": executor_name,
            "Статус": f"{icon} {label}",
        })
    return rows


def _selected_rows(key: str) -> list[int]:
    return st.session_state.get(key, {}).get("selection", {}).get("rows", [])


def _drawer_fields(fields: dict):
    for k, v in fields.items():
        col_k, col_v = st.columns([2, 3])
        col_k.caption(k)
        col_v.markdown(f"**{v}**")


# ── Dialogs ───────────────────────────────────────────────────────────────────


@st.dialog("Отмена доставки")
def _cancel_dialog(delivery: dict):
    order = _get_order(delivery["order_id"])
    customer = order.get("customer_name", f"Заказ #{delivery['order_id']}") if order else f"Заказ #{delivery['order_id']}"
    st.markdown(f"### Отмена — {customer}")
    reason = st.text_area("Причина отмены", placeholder="Укажите причину...")
    if st.button("Подтвердить отмену", type="primary", use_container_width=True):
        if not reason.strip():
            st.error("Укажите причину отмены")
        else:
            try:
                client.post(f"/deliveries/{delivery['id']}/cancel", body={"reason": reason})
                st.rerun()
            except APIError as e:
                _err(e)


@st.dialog("Начать выезд")
def _start_bulk_dialog(batch: list[dict]):
    st.markdown(f"### Начать выезд ({len(batch)} доставок)")
    for d in batch:
        order = _get_order(d["order_id"])
        customer = order.get("customer_name", f"#{d['order_id']}") if order else f"#{d['order_id']}"
        st.write(f"- **{customer}** — {d['planned_date']}")
    st.divider()
    if st.button("Подтвердить выезд", type="primary", use_container_width=True):
        errors = []
        for d in batch:
            try:
                client.post(f"/deliveries/{d['id']}/start")
            except APIError as e:
                errors.append(f"#{d['id']}: {e.detail}")
        if errors:
            st.error("\n".join(errors))
        else:
            st.success(f"Выезд начат для {len(batch)} доставок")
            st.rerun()


# ── Bulk actions ────────────────────────────────��──────────────────────────���──

picked_up_deliveries = [d for d in deliveries if d["status"] == "picked_up"]
if picked_up_deliveries:
    with st.expander(f"Групповой выезд ({len(picked_up_deliveries)} «У водителя»)", expanded=False):
        couriers = sorted(set(d["executor_id"] for d in picked_up_deliveries))
        for cid in couriers:
            courier_name = delivery_user_map.get(cid, f"id={cid}")
            courier_batch = [d for d in picked_up_deliveries if d["executor_id"] == cid]
            st.markdown(f"**{courier_name}** — {len(courier_batch)} доставок")
            selected_ids = []
            for d in courier_batch:
                order = _get_order(d["order_id"])
                customer = order.get("customer_name", f"#{d['order_id']}") if order else f"#{d['order_id']}"
                if st.checkbox(f"{customer} — {d['planned_date']}", key=f"bulk_{d['id']}", value=True):
                    selected_ids.append(d["id"])
            if selected_ids:
                batch = [d for d in courier_batch if d["id"] in selected_ids]
                if st.button(f"Начать выезд ({len(batch)})", key=f"bulk_start_{cid}", type="primary"):
                    _start_bulk_dialog(batch)


# ── Table + Drawer ────────────────────────────────────────────────────────────

if not deliveries:
    st.info("Нет доставок по выбранным фильтрам.")
else:
    import pandas as pd

    table_data = _build_table_data(deliveries)
    df = pd.DataFrame(table_data)

    if _selected_rows("tbl_deliveries"):
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = st.dataframe(
                df, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row", key="tbl_deliveries",
            )
        with col_dr:
            rows = sel.selection.rows
            if rows and rows[0] < len(deliveries):
                delivery = deliveries[rows[0]]
                order = _get_order(delivery["order_id"])
                customer = order.get("customer_name", f"Заказ #{delivery['order_id']}") if order else f"Заказ #{delivery['order_id']}"
                address = order.get("delivery_address", "—") if order else "—"
                executor_name = delivery_user_map.get(delivery["executor_id"], f"id={delivery['executor_id']}")
                icon = DELIVERY_STATUS_ICONS.get(delivery["status"], "")
                label = DELIVERY_STATUS_LABELS.get(delivery["status"], delivery["status"])

                # ── Header ──
                st.markdown(f"### {customer}")
                st.caption(f"{icon} {label}  ·  {delivery['planned_date']}  ·  Курьер {executor_name}")

                # ── Actions ──
                s = delivery["status"]
                if s == "pending":
                    a1, a2 = st.columns(2)
                    if a1.button("Принять", type="primary", use_container_width=True, key="dr_pickup"):
                        try:
                            client.post(f"/deliveries/{delivery['id']}/pick-up")
                            st.rerun()
                        except APIError as e:
                            _err(e)
                    if a2.button("Отменить", use_container_width=True, key="dr_cancel_p"):
                        _cancel_dialog(delivery)

                elif s == "picked_up":
                    a1, a2 = st.columns(2)
                    if a1.button("Начать выезд", type="primary", use_container_width=True, key="dr_start"):
                        try:
                            client.post(f"/deliveries/{delivery['id']}/start")
                            st.rerun()
                        except APIError as e:
                            _err(e)
                    if a2.button("Отменить", use_container_width=True, key="dr_cancel_pu"):
                        _cancel_dialog(delivery)

                elif s == "in_transit":
                    a1, a2 = st.columns(2)
                    if a1.button("Доставлено", type="primary", use_container_width=True, key="dr_complete"):
                        try:
                            client.post(f"/deliveries/{delivery['id']}/complete")
                            st.rerun()
                        except APIError as e:
                            _err(e)
                    if a2.button("Отмена доставки", use_container_width=True, key="dr_cancel_it"):
                        _cancel_dialog(delivery)

                elif s == "completed":
                    st.success(f"Доставлено {delivery.get('completed_at', '')}")

                elif s == "cancelled":
                    st.warning(f"Отменена: {delivery.get('cancellation_reason', '—')}")

                st.divider()

                # ── Section: Заказчик ──
                st.markdown("**ЗАКАЗЧИК**")
                _drawer_fields({"Наименование": customer, "Адрес": address})
                if order and order.get("comment"):
                    _drawer_fields({"Комментарий": order["comment"]})

                st.divider()

                # ── Section: Состав заказа ──
                if order:
                    st.markdown("**СОСТАВ ЗАКАЗА**")
                    try:
                        items = client.get(f"/orders/{delivery['order_id']}/items")
                        for item in items:
                            product_name = item.get("product_name", f"Продукт #{item['product_id']}")
                            qty = item["quantity"]
                            upb = item.get("units_per_box", 1)
                            boxes = qty // upb if upb else qty
                            st.write(f"- {product_name} — {boxes} кор. ({qty} шт)")
                    except APIError:
                        st.caption("Не удалось загрузить состав")

                    st.divider()

                # ── Section: Доставка ──
                st.markdown("**ДОСТАВКА**")
                _drawer_fields({
                    "Курьер": executor_name,
                    "Дата плановая": delivery["planned_date"],
                    "Время начала выезда": delivery.get("started_at") or "—",
                    "Время доставки": delivery.get("completed_at") or "—",
                })
    else:
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            on_select="rerun", selection_mode="single-row", key="tbl_deliveries",
        )


# ── Summary ───────────────────────────────────────────────────────────────────
total = len(deliveries)
in_transit = sum(1 for d in deliveries if d["status"] == "in_transit")
picked_up_count = sum(1 for d in deliveries if d["status"] == "picked_up")
delivered_count = sum(1 for d in deliveries if d["status"] == "completed")
pending_count = sum(1 for d in deliveries if d["status"] == "pending")

parts = [f"Всего: **{total}**"]
if pending_count:
    parts.append(f"Ожидают: **{pending_count}**")
if picked_up_count:
    parts.append(f"У водителя: **{picked_up_count}**")
if in_transit:
    parts.append(f"В пути: **{in_transit}**")
if delivered_count:
    parts.append(f"Доставлено: **{delivered_count}**")

st.caption("   ·   ".join(parts))
