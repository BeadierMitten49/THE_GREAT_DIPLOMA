"""
Страница Справочники — АИС «Ярко» (streamlit_v2).
"""
import pandas as pd
import streamlit as st

from api_client import APIError, get_client

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
.stApp { background: #F5F6F8 !important; }
#MainMenu, header, footer { display: none !important; }
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
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _status(is_active: bool) -> str:
    return "Активна" if is_active else "Деактив."


def _selected_rows(key: str) -> list[int]:
    return st.session_state.get(key, {}).get("selection", {}).get("rows", [])


def _valid_row(tbl_key: str, df: pd.DataFrame) -> int | None:
    rows = _selected_rows(tbl_key)
    if rows and rows[0] < len(df):
        return rows[0]
    return None


def _table(df: pd.DataFrame, key: str):
    return st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
        column_config={"_id": None} if "_id" in df.columns else None,
    )


def _drawer_fields(fields: dict) -> None:
    for k, v in fields.items():
        c1, c2 = st.columns([2, 3])
        c1.caption(k)
        c2.markdown(f"**{v}**")


def _search_filter(key: str) -> tuple[str, str]:
    c1, c2 = st.columns([3, 1])
    search = c1.text_input(
        "Поиск", placeholder="Поиск по наименованию",
        label_visibility="collapsed", key=f"search_{key}",
    )
    status_f = c2.selectbox(
        "Статус", ["Все", "Активные", "Деактивированные"],
        label_visibility="collapsed", key=f"status_{key}",
    )
    return search, status_f


def _apply_filter(df: pd.DataFrame, search: str, status: str, name_col: str = "Наименование") -> pd.DataFrame:
    if search:
        df = df[df[name_col].str.contains(search, case=False, na=False)]
    if status == "Активные":
        df = df[df["Статус"] == "Активна"]
    elif status == "Деактивированные":
        df = df[df["Статус"] == "Деактив."]
    return df.reset_index(drop=True)


def _toggle_button(client, resource: str, item_id: int, is_active: bool, btn_key: str) -> None:
    label = "⏸ Деактивировать" if is_active else "▶ Активировать"
    action = "deactivate" if is_active else "activate"
    if st.button(label, key=btn_key):
        try:
            client.post(f"/references/{resource}/{item_id}/{action}")
            st.rerun()
        except APIError as e:
            st.error(f"Ошибка {e.status_code}: {e.detail}")


def _tab_with_drawer(df: pd.DataFrame, tbl_key: str, drawer_fn, add_btn_label: str | None = None, add_fn=None) -> None:
    """Рендерит таблицу на всю ширину или с drawer при выбранной строке."""
    if add_btn_label:
        c_btn = st.columns([5, 1])
        if c_btn[1].button(f"+ {add_btn_label}", type="primary", use_container_width=True, key=f"add_{tbl_key}"):
            if add_fn:
                add_fn()

    row_idx = _valid_row(tbl_key, df)

    if row_idx is not None:
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(df, tbl_key)
        with col_dr:
            actual_rows = sel.selection.rows
            if actual_rows and actual_rows[0] < len(df):
                drawer_fn(df.iloc[actual_rows[0]])
    else:
        _table(df, tbl_key)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

client = get_client()


def _fetch(path: str) -> list[dict]:
    try:
        return client.get(path, include_inactive=True)
    except APIError as e:
        st.error(f"Ошибка загрузки {path}: {e.detail}")
        return []


raw_materials = _fetch("/references/raw-materials")
packaging     = _fetch("/references/packaging")
products      = _fetch("/references/products")
customers     = _fetch("/references/customers")

rm_map: dict[int, str] = {rm["id"]: rm["name"] for rm in raw_materials}
rm_unit_map: dict[int, str] = {rm["id"]: rm["unit"] for rm in raw_materials}

# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Сырьё")
def _dialog_raw(item: dict | None = None) -> None:
    editing = item is not None
    with st.form("form_raw"):
        name = st.text_input("Наименование", value=item["name"] if editing else "")
        unit = st.text_input("Ед. изм.", value=item["unit"] if editing else "")
        shelf_life = st.number_input(
            "Срок годности (дни)", min_value=1, step=1,
            value=int(item["shelf_life_days"]) if editing else 30,
        )
        critical = st.number_input(
            "Крит. остаток", min_value=0.0, step=0.001, format="%.3f",
            value=float(item["critical_stock"]) if editing else 0.0,
        )
        comment = st.text_input("Комментарий", value=item["comment"] if editing else "")
        submitted = st.form_submit_button("Сохранить")
    if submitted:
        body = {
            "name": name,
            "unit": unit,
            "shelf_life_days": int(shelf_life),
            "critical_stock": critical,
            "comment": comment,
        }
        try:
            if editing:
                client.patch(f"/references/raw-materials/{item['id']}", body=body)
            else:
                client.post("/references/raw-materials", body=body)
            st.rerun()
        except APIError as e:
            st.error(f"Ошибка {e.status_code}: {e.detail}")


@st.dialog("Упаковка")
def _dialog_pack(item: dict | None = None) -> None:
    editing = item is not None
    with st.form("form_pack"):
        name = st.text_input("Наименование", value=item["name"] if editing else "")
        unit = st.text_input("Ед. изм.", value=item["unit"] if editing else "")
        critical = st.number_input(
            "Крит. остаток", min_value=0, step=1,
            value=int(item["critical_stock"]) if editing else 0,
        )
        comment = st.text_input("Комментарий", value=item["comment"] if editing else "")
        submitted = st.form_submit_button("Сохранить")
    if submitted:
        body = {"name": name, "unit": unit, "critical_stock": int(critical), "comment": comment}
        try:
            if editing:
                client.patch(f"/references/packaging/{item['id']}", body=body)
            else:
                client.post("/references/packaging", body=body)
            st.rerun()
        except APIError as e:
            st.error(f"Ошибка {e.status_code}: {e.detail}")


@st.dialog("Продукция")
def _dialog_prod(item: dict | None = None) -> None:
    editing = item is not None
    with st.form("form_prod"):
        name = st.text_input("Наименование", value=item["name"] if editing else "")
        units_per_box = st.number_input(
            "Штук в коробке", min_value=1, step=1,
            value=int(item["units_per_box"]) if editing else 1,
        )
        shelf_life = st.number_input(
            "Срок годности (дни)", min_value=1, step=1,
            value=int(item["shelf_life_days"]) if editing else 30,
        )
        critical = st.number_input(
            "Крит. остаток (шт)", min_value=0, step=1,
            value=int(item["critical_stock"]) if editing else 0,
        )
        submitted = st.form_submit_button("Сохранить")
    if submitted:
        body = {
            "name": name,
            "units_per_box": int(units_per_box),
            "shelf_life_days": int(shelf_life),
            "critical_stock": int(critical),
        }
        try:
            if editing:
                client.patch(f"/references/products/{item['id']}", body=body)
            else:
                client.post("/references/products", body=body)
            st.rerun()
        except APIError as e:
            st.error(f"Ошибка {e.status_code}: {e.detail}")


@st.dialog("Фасовка")
def _dialog_fas(item: dict) -> None:
    with st.form("form_fas"):
        units_per_box = st.number_input(
            "Штук в коробке", min_value=1, step=1,
            value=int(item["units_per_box"]),
        )
        submitted = st.form_submit_button("Сохранить")
    if submitted:
        body = {
            "name": item["name"],
            "units_per_box": int(units_per_box),
            "shelf_life_days": int(item["shelf_life_days"]),
            "critical_stock": int(item["critical_stock"]),
        }
        try:
            client.patch(f"/references/products/{item['id']}", body=body)
            st.rerun()
        except APIError as e:
            st.error(f"Ошибка {e.status_code}: {e.detail}")


@st.dialog("Рецептура")
def _dialog_rec(item: dict) -> None:
    recipe = item.get("recipe", [])
    rm_ids = list(rm_map.keys())

    if not rm_ids:
        st.warning("Сначала добавьте сырьё в справочник")
        return

    st.caption(item["name"])
    n_lines = st.number_input(
        "Количество строк", min_value=1, max_value=20, step=1,
        value=max(len(recipe), 1),
        key="rec_n_lines",
    )
    st.divider()

    c1, c2, c3 = st.columns([3, 2, 2])
    c1.caption("Сырьё")
    c2.caption("Расход/шт")
    c3.caption("Брак %")

    lines_data = []
    for i in range(int(n_lines)):
        c1, c2, c3 = st.columns([3, 2, 2])
        default_rm = recipe[i]["raw_material_id"] if i < len(recipe) else rm_ids[0]
        default_idx = rm_ids.index(default_rm) if default_rm in rm_ids else 0
        rm_id = c1.selectbox(
            f"rm_{i}", options=rm_ids,
            format_func=lambda x: rm_map.get(x, str(x)),
            index=default_idx,
            label_visibility="collapsed",
            key=f"rec_rm_{i}",
        )
        consumption = c2.number_input(
            f"cons_{i}", min_value=0.001, step=0.001, format="%.3f",
            value=float(recipe[i]["consumption_per_unit"]) if i < len(recipe) else 1.0,
            label_visibility="collapsed",
            key=f"rec_cons_{i}",
        )
        waste = c3.number_input(
            f"waste_{i}", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
            value=float(recipe[i]["waste_percentage"]) if i < len(recipe) else 0.0,
            label_visibility="collapsed",
            key=f"rec_waste_{i}",
        )
        lines_data.append({
            "raw_material_id": rm_id,
            "consumption_per_unit": consumption,
            "waste_percentage": waste,
        })

    st.divider()
    if st.button("Сохранить", type="primary", key="rec_save"):
        try:
            client.put(f"/references/products/{item['id']}/recipe", body={"lines": lines_data})
            st.rerun()
        except APIError as e:
            st.error(f"Ошибка {e.status_code}: {e.detail}")


@st.dialog("Заказчик")
def _dialog_cust(item: dict | None = None) -> None:
    editing = item is not None
    with st.form("form_cust"):
        name = st.text_input("Наименование", value=item["name"] if editing else "")
        address = st.text_input("Адрес", value=item["default_address"] if editing else "")
        contact = st.text_input("Контакт", value=item["contact"] if editing else "")
        comment = st.text_input("Комментарий", value=item["comment"] if editing else "")
        submitted = st.form_submit_button("Сохранить")
    if submitted:
        body = {"name": name, "default_address": address, "contact": contact, "comment": comment}
        try:
            if editing:
                client.patch(f"/references/customers/{item['id']}", body=body)
            else:
                client.post("/references/customers", body=body)
            st.rerun()
        except APIError as e:
            st.error(f"Ошибка {e.status_code}: {e.detail}")


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown("## Справочники")
st.caption("Управление справочной информацией системы")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tabs = st.tabs([
    f"Сырьё ({len(raw_materials)})",
    f"Упаковка ({len(packaging)})",
    f"Продукция ({len(products)})",
    f"Фасовка ({len(products)})",
    f"Рецептура ({len(products)})",
    f"Заказчики ({len(customers)})",
])


# ── Tab 1: Сырьё ──────────────────────────────────────────────────────────
with tabs[0]:
    search, status_f = _search_filter("raw")

    df_raw = _apply_filter(pd.DataFrame([
        {
            "_id": r["id"],
            "Наименование": r["name"],
            "Ед. изм.": r["unit"],
            "Крит. остаток": r["critical_stock"],
            "Срок год. (дни)": r["shelf_life_days"],
            "Комментарий": r["comment"],
            "Статус": _status(r["is_active"]),
        }
        for r in raw_materials
    ]), search, status_f)

    def _drawer_raw(row: pd.Series) -> None:
        item_id = int(row["_id"])
        item = next((r for r in raw_materials if r["id"] == item_id), None)
        if not item:
            return
        st.markdown(f"### {item['name']}")
        st.caption(f"ID: {item_id} · {_status(item['is_active'])}")
        if st.button("✏ Редактировать", key=f"edit_raw_{item_id}"):
            _dialog_raw(item)
        _toggle_button(client, "raw-materials", item_id, item["is_active"], f"tog_raw_{item_id}")
        st.divider()
        st.markdown("**АТРИБУТЫ**")
        _drawer_fields({
            "Наименование": item["name"],
            "Единица изм.": item["unit"],
            "Крит. остаток": f"{item['critical_stock']} {item['unit']}",
            "Срок годности": f"{item['shelf_life_days']} дней",
            "Комментарий": item["comment"] or "—",
        })

    _tab_with_drawer(df_raw, "tbl_raw", _drawer_raw, "Добавить сырьё", add_fn=lambda: _dialog_raw())


# ── Tab 2: Упаковка ───────────────────────────────────────────────────────
with tabs[1]:
    search, status_f = _search_filter("pack")

    df_pack = _apply_filter(pd.DataFrame([
        {
            "_id": p["id"],
            "Наименование": p["name"],
            "Ед. изм.": p["unit"],
            "Крит. остаток": p["critical_stock"],
            "Комментарий": p["comment"],
            "Статус": _status(p["is_active"]),
        }
        for p in packaging
    ]), search, status_f)

    def _drawer_pack(row: pd.Series) -> None:
        item_id = int(row["_id"])
        item = next((p for p in packaging if p["id"] == item_id), None)
        if not item:
            return
        st.markdown(f"### {item['name']}")
        st.caption(f"ID: {item_id} · {_status(item['is_active'])}")
        if st.button("✏ Редактировать", key=f"edit_pack_{item_id}"):
            _dialog_pack(item)
        _toggle_button(client, "packaging", item_id, item["is_active"], f"tog_pack_{item_id}")
        st.divider()
        st.markdown("**АТРИБУТЫ**")
        _drawer_fields({
            "Наименование": item["name"],
            "Единица изм.": item["unit"],
            "Крит. остаток": f"{item['critical_stock']} {item['unit']}",
            "Комментарий": item["comment"] or "—",
        })

    _tab_with_drawer(df_pack, "tbl_pack", _drawer_pack, "Добавить упаковку", add_fn=lambda: _dialog_pack())


# ── Tab 3: Продукция ──────────────────────────────────────────────────────
with tabs[2]:
    search, status_f = _search_filter("prod")

    df_prod = _apply_filter(pd.DataFrame([
        {
            "_id": p["id"],
            "Наименование": p["name"],
            "Крит. остаток (шт)": p["critical_stock"],
            "Срок год. (дни)": p["shelf_life_days"],
            "Штук в кор.": p["units_per_box"],
            "Статус": _status(p["is_active"]),
        }
        for p in products
    ]), search, status_f)

    def _drawer_prod(row: pd.Series) -> None:
        item_id = int(row["_id"])
        item = next((p for p in products if p["id"] == item_id), None)
        if not item:
            return
        st.markdown(f"### {item['name']}")
        st.caption(f"ID: {item_id} · {_status(item['is_active'])}")
        if st.button("✏ Редактировать", key=f"edit_prod_{item_id}"):
            _dialog_prod(item)
        _toggle_button(client, "products", item_id, item["is_active"], f"tog_prod_{item_id}")
        st.divider()
        st.markdown("**АТРИБУТЫ**")
        _drawer_fields({
            "Наименование": item["name"],
            "Штук в коробке": str(item["units_per_box"]),
            "Крит. остаток": f"{item['critical_stock']} шт",
            "Срок годности": f"{item['shelf_life_days']} дней",
        })
        recipe = item.get("recipe", [])
        if recipe:
            st.divider()
            st.markdown("**РЕЦЕПТУРА**")
            for line in recipe:
                rm_id = line["raw_material_id"]
                rm_name = rm_map.get(rm_id, f"id={rm_id}")
                rm_unit = rm_unit_map.get(rm_id, "ед")
                c1, c2 = st.columns([3, 2])
                c1.write(rm_name)
                c2.write(f"{line['consumption_per_unit']} {rm_unit}/шт")

    _tab_with_drawer(df_prod, "tbl_prod", _drawer_prod, "Добавить продукт", add_fn=lambda: _dialog_prod())


# ── Tab 4: Фасовка ────────────────────────────────────────────────────────
with tabs[3]:
    search, status_f = _search_filter("fas")

    df_fas = _apply_filter(pd.DataFrame([
        {
            "_id": p["id"],
            "Продукт": p["name"],
            "Штук в коробке": p["units_per_box"],
            "Статус": _status(p["is_active"]),
        }
        for p in products
    ]), search, status_f, name_col="Продукт")

    def _drawer_fas(row: pd.Series) -> None:
        item_id = int(row["_id"])
        item = next((p for p in products if p["id"] == item_id), None)
        if not item:
            return
        st.markdown(f"### {item['name']}")
        st.caption(f"ID: {item_id} · {_status(item['is_active'])}")
        if st.button("✏ Редактировать", key=f"edit_fas_{item_id}"):
            _dialog_fas(item)
        _toggle_button(client, "products", item_id, item["is_active"], f"tog_fas_{item_id}")
        st.divider()
        st.markdown("**АТРИБУТЫ**")
        _drawer_fields({
            "Продукт": item["name"],
            "Штук в коробке": str(item["units_per_box"]),
        })

    _tab_with_drawer(df_fas, "tbl_fas", _drawer_fas)


# ── Tab 5: Рецептура ──────────────────────────────────────────────────────
with tabs[4]:
    search, status_f = _search_filter("rec")

    df_rec = _apply_filter(pd.DataFrame([
        {
            "_id": p["id"],
            "Продукт": p["name"],
            "Кол-во ингредиентов": len(p.get("recipe", [])),
            "Статус": _status(p["is_active"]),
        }
        for p in products
    ]), search, status_f, name_col="Продукт")

    def _drawer_rec(row: pd.Series) -> None:
        item_id = int(row["_id"])
        item = next((p for p in products if p["id"] == item_id), None)
        if not item:
            return
        st.markdown(f"### {item['name']}")
        st.caption(f"ID: {item_id} · {_status(item['is_active'])}")
        if st.button("✏ Редактировать", key=f"edit_rec_{item_id}"):
            _dialog_rec(item)
        _toggle_button(client, "products", item_id, item["is_active"], f"tog_rec_{item_id}")
        st.divider()
        recipe = item.get("recipe", [])
        if recipe:
            st.markdown("**СОСТАВ НА 1 ШТУКУ ПРОДУКТА**")
            for line in recipe:
                rm_id = line["raw_material_id"]
                rm_name = rm_map.get(rm_id, f"id={rm_id}")
                rm_unit = rm_unit_map.get(rm_id, "ед")
                c1, c2 = st.columns([3, 1])
                c1.write(rm_name)
                c2.write(f"{line['consumption_per_unit']} {rm_unit}/шт")
        else:
            st.info("Рецептура не задана")

    _tab_with_drawer(df_rec, "tbl_rec", _drawer_rec)


# ── Tab 6: Заказчики ──────────────────────────────────────────────────────
with tabs[5]:
    search, status_f = _search_filter("cust")

    df_cust = _apply_filter(pd.DataFrame([
        {
            "_id": c["id"],
            "Наименование": c["name"],
            "Адрес": c["default_address"],
            "Контакт": c["contact"],
            "Статус": _status(c["is_active"]),
        }
        for c in customers
    ]), search, status_f)

    def _drawer_cust(row: pd.Series) -> None:
        item_id = int(row["_id"])
        item = next((c for c in customers if c["id"] == item_id), None)
        if not item:
            return
        st.markdown(f"### {item['name']}")
        st.caption(f"ID: {item_id} · {_status(item['is_active'])}")
        if st.button("✏ Редактировать", key=f"edit_cust_{item_id}"):
            _dialog_cust(item)
        _toggle_button(client, "customers", item_id, item["is_active"], f"tog_cust_{item_id}")
        st.divider()
        st.markdown("**АТРИБУТЫ**")
        _drawer_fields({
            "Наименование": item["name"],
            "Адрес": item["default_address"],
            "Контакт": item["contact"] or "—",
            "Комментарий": item["comment"] or "—",
        })

    _tab_with_drawer(df_cust, "tbl_cust", _drawer_cust, "Добавить заказчика", add_fn=lambda: _dialog_cust())
