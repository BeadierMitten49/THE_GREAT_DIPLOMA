import streamlit as st

from api_client import APIError, get_client

st.title("Склад")

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load reference data ───────────────────────────────────────────────────────
try:
    raw_materials_list = client.get("/references/raw-materials", include_inactive=False)
    rm_map = {rm["id"]: f"{rm['name']} ({rm['unit']})" for rm in raw_materials_list}
    packaging_list = client.get("/references/packaging", include_inactive=False)
    pkg_map = {p["id"]: f"{p['name']} ({p['unit']})" for p in packaging_list}
    products = client.get("/references/products", include_inactive=False)
    prod_map = {p["id"]: p["name"] for p in products}
except APIError as e:
    _err(e)
    rm_map = {}
    pkg_map = {}
    prod_map = {}

tab_raw, tab_pkg, tab_prod = st.tabs(["Сырьё", "Упаковка", "Продукция"])

# ── Сырьё ─────────────────────────────────────────────────────────────────────
with tab_raw:
    rm_filter_options = [None] + list(rm_map.keys())
    rm_filter = st.selectbox(
        "Фильтр по сырью",
        options=rm_filter_options,
        format_func=lambda x: rm_map.get(x, "Все") if x else "Все",
        key="wh_rm_filter",
    )
    try:
        raw_stocks = client.get(
            "/warehouse/raw-material-stock",
            raw_material_id=rm_filter,
        )
    except APIError as e:
        _err(e)
        raw_stocks = []

    for s in raw_stocks:
        rm_name = rm_map.get(s["raw_material_id"], f"id={s['raw_material_id']}")
        with st.expander(f"{rm_name} — {s['quantity']} ед. (id={s['id']})"):
            st.write(f"Приход: {s['arrival_date']} | Истекает: {s['expiry_date']}")
            if s.get("comment"):
                st.write(f"Комментарий: {s['comment']}")
            with st.form(f"rm_writeoff_{s['id']}"):
                amount = st.number_input(
                    "Списать (ед.)", min_value=0.001, step=0.001, value=0.001,
                    key=f"rm_wo_amount_{s['id']}",
                )
                if st.form_submit_button("Списать"):
                    try:
                        client.post(
                            f"/warehouse/raw-material-stock/{s['id']}/write-off",
                            body={"amount": amount},
                        )
                        st.success("Списано")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Приход сырья")
    if not rm_map:
        st.info("Сначала добавьте сырьё в справочник.")
    else:
        with st.form("rm_arrival"):
            rm_id = st.selectbox(
                "Сырьё", options=list(rm_map.keys()),
                format_func=lambda x: rm_map[x],
            )
            quantity = st.number_input("Количество", min_value=0.001, step=0.001, value=1.0)
            arrival_date = st.date_input("Дата прихода")
            expiry_date = st.date_input("Дата истечения")
            comment = st.text_input("Комментарий")
            if st.form_submit_button("Оприходовать"):
                try:
                    client.post(
                        "/warehouse/raw-material-stock",
                        body={
                            "raw_material_id": rm_id,
                            "quantity": quantity,
                            "arrival_date": str(arrival_date),
                            "expiry_date": str(expiry_date),
                            "comment": comment if comment else None,
                        },
                    )
                    st.success("Приход зарегистрирован")
                    st.rerun()
                except APIError as e:
                    _err(e)

# ── Упаковка ──────────────────────────────────────────────────────────────────
with tab_pkg:
    pkg_filter_options = [None] + list(pkg_map.keys())
    pkg_filter = st.selectbox(
        "Фильтр по упаковке",
        options=pkg_filter_options,
        format_func=lambda x: pkg_map.get(x, "Все") if x else "Все",
        key="wh_pkg_filter",
    )
    try:
        pkg_stocks = client.get(
            "/warehouse/packaging-stock",
            packaging_id=pkg_filter,
        )
    except APIError as e:
        _err(e)
        pkg_stocks = []

    for s in pkg_stocks:
        pkg_name = pkg_map.get(s["packaging_id"], f"id={s['packaging_id']}")
        with st.expander(f"{pkg_name} — {s['quantity']} шт. (id={s['id']})"):
            if s.get("comment"):
                st.write(f"Комментарий: {s['comment']}")
            with st.form(f"pkg_writeoff_{s['id']}"):
                amount = st.number_input(
                    "Списать (шт.)", min_value=1, value=1,
                    key=f"pkg_wo_amount_{s['id']}",
                )
                if st.form_submit_button("Списать"):
                    try:
                        client.post(
                            f"/warehouse/packaging-stock/{s['id']}/write-off",
                            body={"amount": amount},
                        )
                        st.success("Списано")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Приход упаковки")
    if not pkg_map:
        st.info("Сначала добавьте упаковку в справочник.")
    else:
        with st.form("pkg_arrival"):
            pkg_id = st.selectbox(
                "Упаковка", options=list(pkg_map.keys()),
                format_func=lambda x: pkg_map[x],
            )
            quantity = st.number_input("Количество (шт.)", min_value=1, value=1)
            comment = st.text_input("Комментарий")
            if st.form_submit_button("Оприходовать"):
                try:
                    client.post(
                        "/warehouse/packaging-stock",
                        body={
                            "packaging_id": pkg_id,
                            "quantity": quantity,
                            "comment": comment if comment else None,
                        },
                    )
                    st.success("Приход зарегистрирован")
                    st.rerun()
                except APIError as e:
                    _err(e)

# ── Продукция ─────────────────────────────────────────────────────────────────
with tab_prod:
    prod_filter_options = [None] + list(prod_map.keys())
    prod_filter = st.selectbox(
        "Фильтр по товару",
        options=prod_filter_options,
        format_func=lambda x: prod_map.get(x, "Все") if x else "Все",
        key="wh_prod_filter",
    )
    try:
        prod_stocks = client.get(
            "/warehouse/product-stock",
            product_id=prod_filter,
        )
    except APIError as e:
        _err(e)
        prod_stocks = []

    for s in prod_stocks:
        prod_name = prod_map.get(s["product_id"], f"id={s['product_id']}")
        with st.expander(
            f"{prod_name} — {s['quantity']} шт. | "
            f"Партия {s['batch_number']}/{s['batch_year']} | "
            f"до {s['expiry_date']} (id={s['id']})"
        ):
            st.write(f"Приход: {s['arrival_date']}")
            if s.get("comment"):
                st.write(f"Комментарий: {s['comment']}")
            if is_director:
                with st.form(f"prod_writeoff_{s['id']}"):
                    amount = st.number_input(
                        "Списать (шт.)", min_value=1, value=1,
                        key=f"prod_wo_amount_{s['id']}",
                    )
                    if st.form_submit_button("Списать (директор)"):
                        try:
                            client.post(
                                f"/warehouse/product-stock/{s['id']}/write-off",
                                body={"amount": amount},
                            )
                            st.success("Списано")
                            st.rerun()
                        except APIError as e:
                            _err(e)

    st.divider()
    st.subheader("Приход продукции")
    if not prod_map:
        st.info("Сначала добавьте товары в справочник.")
    else:
        with st.form("prod_arrival"):
            prod_id = st.selectbox(
                "Товар", options=list(prod_map.keys()),
                format_func=lambda x: prod_map[x],
            )
            quantity = st.number_input("Количество (шт.)", min_value=1, value=1)
            arrival_date = st.date_input("Дата прихода")
            expiry_date = st.date_input("Дата истечения")
            comment = st.text_input("Комментарий")
            if st.form_submit_button("Оприходовать"):
                try:
                    client.post(
                        "/warehouse/product-stock",
                        body={
                            "product_id": prod_id,
                            "quantity": quantity,
                            "arrival_date": str(arrival_date),
                            "expiry_date": str(expiry_date),
                            "comment": comment if comment else None,
                        },
                    )
                    st.success("Приход зарегистрирован")
                    st.rerun()
                except APIError as e:
                    _err(e)
