import streamlit as st

from api_client import APIError, get_client

st.title("Справочники")

client = get_client()


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


tab_customers, tab_products, tab_raw, tab_packaging = st.tabs(
    ["Клиенты", "Товары", "Сырьё", "Упаковка"]
)

# ── Клиенты ──────────────────────────────────────────────────────────────────
with tab_customers:
    show_inactive = st.checkbox("Показать неактивных", key="cust_inactive")
    try:
        customers = client.get("/references/customers", include_inactive=show_inactive)
    except APIError as e:
        _err(e)
        customers = []

    for c in customers:
        status_icon = "🟢" if c["is_active"] else "🔴"
        with st.expander(f"{status_icon} {c['name']} (id={c['id']})"):
            st.write(f"Адрес: {c['default_address']}")
            col1, col2 = st.columns(2)
            if c["is_active"]:
                if col1.button("Деактивировать", key=f"cust_deact_{c['id']}"):
                    try:
                        client.post(f"/references/customers/{c['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if col1.button("Активировать", key=f"cust_act_{c['id']}"):
                    try:
                        client.post(f"/references/customers/{c['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Добавить клиента")
    with st.form("create_customer"):
        name = st.text_input("Название")
        address = st.text_input("Адрес по умолчанию")
        if st.form_submit_button("Создать"):
            try:
                client.post(
                    "/references/customers",
                    body={"name": name, "default_address": address},
                )
                st.success("Клиент создан")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Товары ────────────────────────────────────────────────────────────────────
with tab_products:
    show_inactive_p = st.checkbox("Показать неактивные", key="prod_inactive")
    try:
        products = client.get("/references/products", include_inactive=show_inactive_p)
        raw_materials_list = client.get("/references/raw-materials", include_inactive=False)
        rm_map = {rm["id"]: rm["name"] for rm in raw_materials_list}
    except APIError as e:
        _err(e)
        products = []
        rm_map = {}

    for p in products:
        status_icon = "🟢" if p["is_active"] else "🔴"
        with st.expander(f"{status_icon} {p['name']} (id={p['id']})"):
            st.write(
                f"Ед/упак: {p['units_per_box']} | "
                f"Срок хранения: {p['shelf_life_days']} дн. | "
                f"Крит. остаток: {p['critical_stock']}"
            )
            if p["is_active"]:
                if st.button("Деактивировать", key=f"prod_deact_{p['id']}"):
                    try:
                        client.post(f"/references/products/{p['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if st.button("Активировать", key=f"prod_act_{p['id']}"):
                    try:
                        client.post(f"/references/products/{p['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

            with st.expander("Рецептура", expanded=False):
                recipe = p.get("recipe", [])
                if recipe:
                    for line in recipe:
                        rm_name = rm_map.get(line["raw_material_id"], f"id={line['raw_material_id']}")
                        st.write(
                            f"- {rm_name}: {line['consumption_per_unit']} ед/шт, "
                            f"брак {line['waste_percentage']}%"
                        )
                else:
                    st.write("Рецептура не задана")

                st.write("**Заменить рецептуру:**")
                if rm_map:
                    n_lines = st.number_input(
                        "Количество строк", min_value=1, max_value=20, value=1,
                        key=f"recipe_n_{p['id']}",
                    )
                    recipe_lines = []
                    rm_ids = list(rm_map.keys())
                    for i in range(int(n_lines)):
                        c1, c2, c3 = st.columns(3)
                        rm_id = c1.selectbox(
                            "Сырьё", options=rm_ids,
                            format_func=lambda x: rm_map.get(x, x),
                            key=f"recipe_rm_{p['id']}_{i}",
                        )
                        consumption = c2.number_input(
                            "Расход (ед/шт)", min_value=0.001, value=1.0, step=0.001,
                            key=f"recipe_cons_{p['id']}_{i}",
                        )
                        waste = c3.number_input(
                            "Брак %", min_value=0.0, max_value=100.0, value=0.0,
                            key=f"recipe_waste_{p['id']}_{i}",
                        )
                        recipe_lines.append({
                            "raw_material_id": rm_id,
                            "consumption_per_unit": consumption,
                            "waste_percentage": waste,
                        })
                    if st.button("Сохранить рецептуру", key=f"recipe_save_{p['id']}"):
                        try:
                            client.put(
                                f"/references/products/{p['id']}/recipe",
                                body={"lines": recipe_lines},
                            )
                            st.success("Рецептура обновлена")
                            st.rerun()
                        except APIError as e:
                            _err(e)
                else:
                    st.info("Сначала добавьте сырьё в справочник.")

    st.divider()
    st.subheader("Добавить товар")
    with st.form("create_product"):
        name = st.text_input("Название")
        upb = st.number_input("Ед/упак", min_value=1, value=1)
        sld = st.number_input("Срок хранения (дни)", min_value=1, value=30)
        cs = st.number_input("Критический остаток", min_value=0, value=0)
        if st.form_submit_button("Создать"):
            try:
                client.post(
                    "/references/products",
                    body={
                        "name": name,
                        "units_per_box": upb,
                        "shelf_life_days": sld,
                        "critical_stock": cs,
                    },
                )
                st.success("Товар создан")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Сырьё ─────────────────────────────────────────────────────────────────────
with tab_raw:
    show_inactive_rm = st.checkbox("Показать неактивные", key="rm_inactive")
    try:
        rms = client.get("/references/raw-materials", include_inactive=show_inactive_rm)
    except APIError as e:
        _err(e)
        rms = []

    for rm in rms:
        status_icon = "🟢" if rm["is_active"] else "🔴"
        with st.expander(f"{status_icon} {rm['name']} ({rm['unit']}) (id={rm['id']})"):
            st.write(
                f"Срок хранения: {rm['shelf_life_days']} дн. | "
                f"Крит. остаток: {rm['critical_stock']}"
            )
            if rm["is_active"]:
                if st.button("Деактивировать", key=f"rm_deact_{rm['id']}"):
                    try:
                        client.post(f"/references/raw-materials/{rm['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if st.button("Активировать", key=f"rm_act_{rm['id']}"):
                    try:
                        client.post(f"/references/raw-materials/{rm['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Добавить сырьё")
    with st.form("create_rm"):
        name = st.text_input("Название")
        unit = st.text_input("Единица измерения", value="кг")
        sld = st.number_input("Срок хранения (дни)", min_value=1, value=30)
        cs = st.number_input("Критический остаток", min_value=0.0, value=0.0, step=0.1)
        if st.form_submit_button("Создать"):
            try:
                client.post(
                    "/references/raw-materials",
                    body={
                        "name": name,
                        "unit": unit,
                        "shelf_life_days": sld,
                        "critical_stock": cs,
                    },
                )
                st.success("Сырьё добавлено")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Упаковка ──────────────────────────────────────────────────────────────────
with tab_packaging:
    show_inactive_pk = st.checkbox("Показать неактивные", key="pk_inactive")
    try:
        packagings = client.get("/references/packaging", include_inactive=show_inactive_pk)
    except APIError as e:
        _err(e)
        packagings = []

    for pk in packagings:
        status_icon = "🟢" if pk["is_active"] else "🔴"
        with st.expander(f"{status_icon} {pk['name']} ({pk['unit']}) (id={pk['id']})"):
            st.write(f"Крит. остаток: {pk['critical_stock']}")
            if pk["is_active"]:
                if st.button("Деактивировать", key=f"pk_deact_{pk['id']}"):
                    try:
                        client.post(f"/references/packaging/{pk['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if st.button("Активировать", key=f"pk_act_{pk['id']}"):
                    try:
                        client.post(f"/references/packaging/{pk['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Добавить упаковку")
    with st.form("create_pk"):
        name = st.text_input("Название")
        unit = st.text_input("Единица", value="шт")
        cs = st.number_input("Критический остаток", min_value=0, value=0)
        if st.form_submit_button("Создать"):
            try:
                client.post(
                    "/references/packaging",
                    body={"name": name, "unit": unit, "critical_stock": cs},
                )
                st.success("Упаковка добавлена")
                st.rerun()
            except APIError as e:
                _err(e)
