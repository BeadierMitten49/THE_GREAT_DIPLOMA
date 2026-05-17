import streamlit as st

from api_client import APIError, get_client

st.title("Заказы")

client = get_client()


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load reference data ───────────────────────────────────────────────────────
try:
    customers = client.get("/references/customers", include_inactive=False)
    customer_map = {c["id"]: c["name"] for c in customers}
    products = client.get("/references/products", include_inactive=False)
    product_map = {p["id"]: p["name"] for p in products}
    users = client.get("/users")
    delivery_users = [u for u in users if "delivery" in u.get("roles", [])]
    delivery_user_map = {u["id"]: u["full_name"] for u in delivery_users}
except APIError as e:
    _err(e)
    customer_map = {}
    product_map = {}
    delivery_user_map = {}

# ── Filters ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
status_filter = col1.selectbox(
    "Статус",
    options=["", "new", "confirmed", "assembly", "delivery", "completed", "cancelled"],
    format_func=lambda x: x if x else "Все",
)
customer_filter_options = [""] + list(customer_map.keys())
customer_filter = col2.selectbox(
    "Клиент",
    options=customer_filter_options,
    format_func=lambda x: customer_map.get(x, "Все") if x else "Все",
)

# ── Order list ────────────────────────────────────────────────────────────────
try:
    orders = client.get(
        "/orders",
        status=status_filter if status_filter else None,
        customer_id=customer_filter if customer_filter else None,
    )
except APIError as e:
    _err(e)
    orders = []

for o in orders:
    cust_name = customer_map.get(o["customer_id"], f"id={o['customer_id']}")
    label = f"#{o['number']} — {cust_name} — {o['status']} — {o['delivery_date']}"
    with st.expander(label):
        st.write(f"Адрес: {o['delivery_address']}")
        if o.get("comment"):
            st.write(f"Комментарий: {o['comment']}")
        if o.get("delivery_user_id"):
            st.write(f"Водитель: {delivery_user_map.get(o['delivery_user_id'], o['delivery_user_id'])}")

        # Items
        try:
            items = client.get(f"/orders/{o['id']}/items")
        except APIError:
            items = []
        if items:
            st.write("**Позиции:**")
            for item in items:
                prod_name = product_map.get(item["product_id"], f"id={item['product_id']}")
                st.write(f"- {prod_name}: {item['quantity']} шт.")

        # Status change
        new_status = st.selectbox(
            "Сменить статус",
            options=["", "new", "confirmed", "assembly", "delivery", "completed", "cancelled"],
            format_func=lambda x: x if x else "— не менять —",
            key=f"order_status_{o['id']}",
        )
        if new_status and st.button("Применить статус", key=f"order_apply_status_{o['id']}"):
            try:
                client.patch(f"/orders/{o['id']}/status", body={"new_status": new_status})
                st.success("Статус изменён")
                st.rerun()
            except APIError as e:
                _err(e)

        # Delete
        if st.button("Удалить заказ", key=f"order_del_{o['id']}"):
            try:
                client.delete(f"/orders/{o['id']}")
                st.success("Заказ удалён")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Create order ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("Создать заказ")

if not customer_map or not product_map:
    st.info("Для создания заказа необходимы клиенты и товары в справочниках.")
else:
    with st.form("create_order"):
        cust_id = st.selectbox(
            "Клиент",
            options=list(customer_map.keys()),
            format_func=lambda x: customer_map[x],
        )
        address = st.text_input("Адрес доставки")
        delivery_date = st.date_input("Дата доставки")
        comment = st.text_input("Комментарий", value="")

        driver_options = [None] + list(delivery_user_map.keys())
        driver_id = st.selectbox(
            "Водитель (необязательно)",
            options=driver_options,
            format_func=lambda x: delivery_user_map.get(x, "— не назначен —") if x else "— не назначен —",
        )

        st.write("**Позиции заказа:**")
        n_items = st.number_input("Количество позиций", min_value=1, max_value=50, value=1)
        items = []
        prod_ids = list(product_map.keys())
        for i in range(int(n_items)):
            c1, c2 = st.columns(2)
            pid = c1.selectbox(
                "Товар", options=prod_ids,
                format_func=lambda x: product_map.get(x, x),
                key=f"order_prod_{i}",
            )
            qty = c2.number_input("Кол-во", min_value=1, value=1, key=f"order_qty_{i}")
            items.append({"product_id": pid, "quantity": qty})

        if st.form_submit_button("Создать заказ"):
            try:
                client.post(
                    "/orders",
                    body={
                        "customer_id": cust_id,
                        "delivery_address": address,
                        "delivery_date": str(delivery_date),
                        "items": items,
                        "delivery_user_id": driver_id,
                        "comment": comment if comment else None,
                    },
                )
                st.success("Заказ создан")
                st.rerun()
            except APIError as e:
                _err(e)
