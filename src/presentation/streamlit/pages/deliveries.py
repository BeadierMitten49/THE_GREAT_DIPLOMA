import streamlit as st

from api_client import APIError, get_client

st.title("Доставки")

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load reference data ───────────────────────────────────────────────────────
try:
    if is_director:
        users = client.get("/users")
        delivery_users = [u for u in users if "delivery" in u.get("roles", [])]
        delivery_user_map = {u["id"]: u["full_name"] for u in delivery_users}
    else:
        delivery_user_map = {}
except APIError as e:
    _err(e)
    delivery_user_map = {}

# ── Filters ───────────────────────────────────────────────────────────────────
status_filter = st.selectbox(
    "Статус",
    options=["", "pending", "picked_up", "in_transit", "completed", "cancelled"],
    format_func=lambda x: x if x else "Все",
)

# ── Delivery list ─────────────────────────────────────────────────────────────
try:
    deliveries = client.get(
        "/deliveries",
        status=status_filter if status_filter else None,
    )
except APIError as e:
    _err(e)
    deliveries = []

for d in deliveries:
    executor_name = delivery_user_map.get(d["executor_id"], f"id={d['executor_id']}")
    label = (
        f"Заказ #{d['order_id']} — {d['status']} — "
        f"{d['planned_date']} — {executor_name}"
    )
    with st.expander(label):
        if d.get("started_at"):
            st.write(f"Выехал: {d['started_at']}")
        if d.get("completed_at"):
            st.write(f"Завершена: {d['completed_at']}")
        if d.get("cancellation_reason"):
            st.write(f"Причина отмены: {d['cancellation_reason']}")

        s = d["status"]

        if s == "pending":
            col1, col2 = st.columns(2)
            if col1.button("Принять", key=f"del_pickup_{d['id']}"):
                try:
                    client.post(f"/deliveries/{d['id']}/pick-up")
                    st.rerun()
                except APIError as e:
                    _err(e)
            if col2.button("Отменить", key=f"del_cancel_btn_{d['id']}"):
                st.session_state[f"del_cancel_open_{d['id']}"] = True
            if st.session_state.get(f"del_cancel_open_{d['id']}"):
                with st.form(f"del_cancel_form_{d['id']}"):
                    reason = st.text_input("Причина отмены")
                    if st.form_submit_button("Подтвердить"):
                        try:
                            client.post(
                                f"/deliveries/{d['id']}/cancel",
                                body={"reason": reason},
                            )
                            st.session_state.pop(f"del_cancel_open_{d['id']}", None)
                            st.rerun()
                        except APIError as e:
                            _err(e)

        elif s == "picked_up":
            col1, col2 = st.columns(2)
            if col1.button("Выехал", key=f"del_start_{d['id']}"):
                try:
                    client.post(f"/deliveries/{d['id']}/start")
                    st.rerun()
                except APIError as e:
                    _err(e)
            if col2.button("Отменить", key=f"del_cancel_btn2_{d['id']}"):
                st.session_state[f"del_cancel_open2_{d['id']}"] = True
            if st.session_state.get(f"del_cancel_open2_{d['id']}"):
                with st.form(f"del_cancel_form2_{d['id']}"):
                    reason = st.text_input("Причина отмены")
                    if st.form_submit_button("Подтвердить"):
                        try:
                            client.post(
                                f"/deliveries/{d['id']}/cancel",
                                body={"reason": reason},
                            )
                            st.session_state.pop(f"del_cancel_open2_{d['id']}", None)
                            st.rerun()
                        except APIError as e:
                            _err(e)

        elif s == "in_transit":
            if st.button("Завершить доставку", key=f"del_complete_{d['id']}"):
                try:
                    client.post(f"/deliveries/{d['id']}/complete")
                    st.rerun()
                except APIError as e:
                    _err(e)

# ── Create delivery (director only) ──────────────────────────────────────────
if is_director:
    st.divider()
    st.subheader("Создать доставку")
    if not delivery_user_map:
        st.info("Нет водителей (пользователей с ролью delivery).")
    else:
        with st.form("create_delivery"):
            order_id = st.number_input("ID заказа", min_value=1, value=1)
            executor_id = st.selectbox(
                "Водитель",
                options=list(delivery_user_map.keys()),
                format_func=lambda x: delivery_user_map[x],
            )
            planned_date = st.date_input("Плановая дата")
            if st.form_submit_button("Создать"):
                try:
                    client.post(
                        "/deliveries",
                        body={
                            "order_id": order_id,
                            "executor_id": executor_id,
                            "planned_date": str(planned_date),
                        },
                    )
                    st.success("Доставка создана")
                    st.rerun()
                except APIError as e:
                    _err(e)
