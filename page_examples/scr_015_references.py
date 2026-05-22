"""
SCR-015 — Справочники
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_015_references.py
"""
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SCR-015 — Справочники (демо)",
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
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 20px;
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
# Mock data
# ---------------------------------------------------------------------------

RAW_MATERIALS = pd.DataFrame([
    ["Молоко цельное",              "кг",  100,  5,   "",                         "Активна"],
    ["Молоко обезжиренное",         "кг",  100,  5,   "",                         "Активна"],
    ["Сахар-песок",                 "кг",   50, 730,  "",                         "Активна"],
    ["Соль пищевая",                "кг",   10, 730,  "",                         "Активна"],
    ["Стабилизатор «Юнипектин»",    "кг",    1, 180,  "Поставщик: «АромаТех»",    "Активна"],
    ["Закваска кефирная",           "кг",    2,  90,  "Хранить +2..+8°C",         "Активна"],
    ["Сливки 33%",                  "кг",   15,   7,  "",                         "Активна"],
    ["Йогуртовая закваска «Био»",   "кг",    1,  60,  "Снято с производства",     "Деактив."],
], columns=["Наименование", "Ед. изм.", "Крит. остаток", "Срок год. (дни)", "Комментарий", "Статус"])

PACKAGING = pd.DataFrame([
    ["Tetra Pak 1 л",              "шт",  500, "Поставщик: TetraPak RU", "Активна"],
    ["Стакан 200 мл с крышкой",    "шт",  500, "",                       "Активна"],
    ["Бутылка ПЭТ 0,9 л",         "шт",  300, "",                       "Активна"],
    ["Этикетка «Молоко 3,2%»",    "шт", 1000, "",                       "Активна"],
    ["Плёнка термоусадочная",      "м",    50, "Рулон 100 м",            "Активна"],
    ["Короб гофро 30×20×15",       "шт",  100, "",                       "Активна"],
    ["Крышка для ПЭТ-бутылки",    "шт",  300, "",                       "Активна"],
], columns=["Наименование", "Ед. изм.", "Крит. остаток", "Комментарий", "Статус"])

PRODUCTS = pd.DataFrame([
    ["Молоко 3,2% 1 л",                    100,  7, "Tetra Pak 1 л · 12 шт/кор",    "Активна"],
    ["Молоко обезжиренное 1 л",            100,  7, "Tetra Pak 1 л · 12 шт/кор",    "Активна"],
    ["Кефир 1% 1 л",                       100,  7, "Tetra Pak 1 л · 12 шт/кор",    "Активна"],
    ["Сметана 20% 200 г",                   50, 14, "Стакан 200 мл · 24 шт/кор",    "Активна"],
    ["Творог 9%",                           40,  5, "Стакан 200 мл · 24 шт/кор",    "Активна"],
    ["Йогурт «Питьевой» клубника 0,9 л",   60, 14, "Бутылка ПЭТ 0,9 л · 12 шт/кор","Активна"],
], columns=["Наименование", "Крит. остаток (шт)", "Срок год. (дни)", "Фасовка по умолчанию", "Статус"])

PACKAGING_SIZES = pd.DataFrame([
    ["Молоко 3,2% 1 л",            12, "Активна"],
    ["Кефир 1% 1 л",               12, "Активна"],
    ["Сметана 20% 200 г",          24, "Активна"],
    ["Йогурт «Питьевой» 0,9 л",   12, "Активна"],
], columns=["Продукт", "Штук в коробке", "Статус"])

RECIPES = pd.DataFrame([
    ["Молоко 3,2% 1 л",                    3, "Активна"],
    ["Молоко обезжиренное 1 л",            3, "Активна"],
    ["Кефир 1% 1 л",                       4, "Активна"],
    ["Сметана 20% 200 г",                  2, "Активна"],
    ["Творог 9%",                          2, "Активна"],
    ["Йогурт «Питьевой» клубника 0,9 л",  5, "Активна"],
], columns=["Продукт", "Кол-во ингредиентов", "Статус"])

CUSTOMERS = pd.DataFrame([
    ["Магнит, ТТ Авиаторов",        "г. Красноярск, ул. Авиаторов, 25",              "+7 (391) 555-12-34", "Активна"],
    ["Магнит, ТТ Северный",         "г. Красноярск, ул. 9 Мая, 77",                  "+7 (391) 555-12-35", "Активна"],
    ["Пятёрочка, ТТ Калинина",      "г. Красноярск, ул. Калинина, 64",               "+7 (391) 222-44-55", "Активна"],
    ["Пятёрочка, ТТ Свободный",     "г. Красноярск, пр. Свободный, 64",              "+7 (391) 222-44-56", "Активна"],
    ["Лента, ТТ Взлётка",           "г. Красноярск, ул. Взлётная, 5",                "+7 (391) 333-66-77", "Активна"],
    ["ИП Соколова О.В.",            "г. Красноярск, ул. Бограда, 14",                "+7 (902) 911-23-45", "Активна"],
    ["ИП Гаврилов А.С.",            "г. Красноярск, ул. Партизана Железняка, 17",    "+7 (902) 911-77-88", "Активна"],
    ["ООО «Кафе-бар»",              "г. Красноярск, ул. Маркса, 102",                "+7 (391) 444-55-66", "Активна"],
    ["ИП Морозов Д.К.",             "г. Красноярск, пр. Свободный, 92",              "+7 (902) 911-99-00", "Деактив."],
], columns=["Наименование", "Адрес", "Контакт", "Статус"])

# Детали для drawer (mock)
DRAWER_DETAILS = {
    "raw": {
        "Молоко цельное": {
            "meta": "ID: RM-01 · Создана 12.04.2025 · Тихомиров Е.С.",
            "fields": {"Наименование": "Молоко цельное", "Единица измерения": "кг",
                       "Критический остаток": "100 кг", "Срок годности": "5 дней с даты поступления", "Комментарий": "—"},
        },
    },
    "packaging": {
        "Tetra Pak 1 л": {
            "meta": "ID: PK-01 · Создана 10.04.2025 · Тихомиров Е.С.",
            "fields": {"Наименование": "Tetra Pak 1 л", "Единица измерения": "шт",
                       "Критический остаток": "500 шт", "Комментарий": "Поставщик: TetraPak RU"},
        },
    },
    "recipe": {
        "Кефир 1% 1 л": {
            "meta": "Рецептура · ID: RC-03 · Создана 15.04.2025",
            "ingredients": [
                ("Молоко цельное",          "1,000 л"),
                ("Закваска кефирная",       "0,005 кг"),
                ("Сахар-песок",             "0,015 кг"),
                ("Стабилизатор «Юнипектин»","0,002 кг"),
            ],
        },
    },
    "customer": {
        "Магнит, ТТ Авиаторов": {
            "meta": "Заказчик · ID: CL-04 · Создана 22.03.2025",
            "fields": {"Наименование": "Магнит, ТТ Авиаторов",
                       "Адрес": "г. Красноярск, ул. Авиаторов, 25",
                       "Контакт": "+7 (391) 555-12-34",
                       "Комментарий": "Звонить за час до доставки. Приёмка с 7:00 до 11:00."},
        },
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _table(df: pd.DataFrame, key: str):
    """Таблица с выбором строки."""
    return st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )


def _selected_rows(key: str) -> list[int]:
    """Читает текущий выбор из session_state (до рендера виджета)."""
    return st.session_state.get(key, {}).get("selection", {}).get("rows", [])


def _drawer_fields(fields: dict):
    for k, v in fields.items():
        col_k, col_v = st.columns([2, 3])
        col_k.caption(k)
        col_v.markdown(f"**{v}**")


def _search_and_filter(key: str):
    c1, c2 = st.columns([3, 1])
    c1.text_input("Поиск", placeholder="Поиск по наименованию", label_visibility="collapsed", key=f"search_{key}")
    c2.selectbox("Статус", ["Все", "Активные", "Деактивированные"], label_visibility="collapsed", key=f"status_{key}")


def _header(title: str, btn_label: str):
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f"## Справочники")
        st.caption("Управление справочной информацией системы")
    with c2:
        st.button(f"+ {btn_label}", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

st.markdown("## Справочники")
st.caption("Управление справочной информацией системы")

tabs = st.tabs(["Сырьё (8)", "Упаковка (7)", "Продукция (6)", "Фасовка (4)", "Рецептура (6)", "Заказчики (12)"])


# ── Tab 1: Сырьё ──────────────────────────────────────────────────────────
with tabs[0]:
    c_btn = st.columns([5, 1])
    c_btn[1].button("+ Добавить сырьё", type="primary", use_container_width=True, key="add_raw")
    _search_and_filter("raw")

    if _selected_rows("tbl_raw"):
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(RAW_MATERIALS, key="tbl_raw")
        with col_dr:
            rows = sel.selection.rows
            if rows:
                name = RAW_MATERIALS.iloc[rows[0]]["Наименование"]
                detail = DRAWER_DETAILS["raw"].get(name)
                st.markdown(f"### {name}")
                st.caption(detail["meta"] if detail else "")
                st.button("✏ Редактировать", key="edit_raw")
                st.button("⏸ Деактивировать", key="deact_raw")
                st.divider()
                st.markdown("**АТРИБУТЫ**")
                if detail:
                    _drawer_fields(detail["fields"])
    else:
        _table(RAW_MATERIALS, key="tbl_raw")


# ── Tab 2: Упаковка ───────────────────────────────────────────────────────
with tabs[1]:
    c_btn = st.columns([5, 1])
    c_btn[1].button("+ Добавить упаковку", type="primary", use_container_width=True, key="add_pack")
    _search_and_filter("pack")

    if _selected_rows("tbl_pack"):
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(PACKAGING, key="tbl_pack")
        with col_dr:
            rows = sel.selection.rows
            if rows:
                name = PACKAGING.iloc[rows[0]]["Наименование"]
                detail = DRAWER_DETAILS["packaging"].get(name)
                st.markdown(f"### {name}")
                st.caption(detail["meta"] if detail else "")
                st.button("✏ Редактировать", key="edit_pack")
                st.button("⏸ Деактивировать", key="deact_pack")
                st.divider()
                st.markdown("**АТРИБУТЫ**")
                if detail:
                    _drawer_fields(detail["fields"])
    else:
        _table(PACKAGING, key="tbl_pack")


# ── Tab 3: Продукция ──────────────────────────────────────────────────────
with tabs[2]:
    c_btn = st.columns([5, 1])
    c_btn[1].button("+ Добавить продукт", type="primary", use_container_width=True, key="add_prod")
    _search_and_filter("prod")

    if _selected_rows("tbl_prod"):
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(PRODUCTS, key="tbl_prod")
        with col_dr:
            rows = sel.selection.rows
            if rows:
                name = PRODUCTS.iloc[rows[0]]["Наименование"]
                st.markdown(f"### {name}")
                st.caption("ID: PR-01 · Создана 12.04.2025")
                st.button("✏ Редактировать", key="edit_prod")
                st.button("⏸ Деактивировать", key="deact_prod")
                st.divider()
                row = PRODUCTS.iloc[rows[0]]
                st.markdown("**АТРИБУТЫ**")
                _drawer_fields({
                    "Наименование": name,
                    "Критический остаток": f"{row['Крит. остаток (шт)']} шт",
                    "Срок годности": f"{row['Срок год. (дни)']} дней с даты приёмки",
                    "Фасовка по умолчанию": row["Фасовка по умолчанию"],
                })
    else:
        _table(PRODUCTS, key="tbl_prod")


# ── Tab 4: Фасовка ────────────────────────────────────────────────────────
with tabs[3]:
    c_btn = st.columns([5, 1])
    c_btn[1].button("+ Добавить фасовку", type="primary", use_container_width=True, key="add_fas")
    _search_and_filter("fas")

    if _selected_rows("tbl_fas"):
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(PACKAGING_SIZES, key="tbl_fas")
        with col_dr:
            rows = sel.selection.rows
            if rows:
                row = PACKAGING_SIZES.iloc[rows[0]]
                st.markdown(f"### {row['Продукт']}")
                st.caption("Фасовка · ID: FS-01 · Создана 12.04.2025")
                st.button("✏ Редактировать", key="edit_fas")
                st.button("⏸ Деактивировать", key="deact_fas")
                st.divider()
                st.markdown("**АТРИБУТЫ**")
                _drawer_fields({"Продукт": row["Продукт"], "Штук в коробке": str(row["Штук в коробке"])})
    else:
        _table(PACKAGING_SIZES, key="tbl_fas")


# ── Tab 5: Рецептура ──────────────────────────────────────────────────────
with tabs[4]:
    c_btn = st.columns([5, 1])
    c_btn[1].button("+ Добавить рецептуру", type="primary", use_container_width=True, key="add_rec")
    _search_and_filter("rec")

    if _selected_rows("tbl_rec"):
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(RECIPES, key="tbl_rec")
        with col_dr:
            rows = sel.selection.rows
            if rows:
                name = RECIPES.iloc[rows[0]]["Продукт"]
                detail = DRAWER_DETAILS["recipe"].get(name)
                st.markdown(f"### {name}")
                st.caption(detail["meta"] if detail else "Рецептура")
                st.button("✏ Редактировать", key="edit_rec")
                st.button("⏸ Деактивировать", key="deact_rec")
                st.divider()
                st.markdown("**СОСТАВ НА 1 ШТУКУ ПРОДУКТА**")
                if detail:
                    for ingredient, qty in detail["ingredients"]:
                        c1, c2 = st.columns([3, 1])
                        c1.write(ingredient)
                        c2.write(qty)
                else:
                    row = RECIPES.iloc[rows[0]]
                    st.info(f"{row['Кол-во ингредиентов']} ингредиентов (детали не добавлены в демо)")
    else:
        _table(RECIPES, key="tbl_rec")


# ── Tab 6: Заказчики ──────────────────────────────────────────────────────
with tabs[5]:
    c_btn = st.columns([5, 1])
    c_btn[1].button("+ Добавить заказчика", type="primary", use_container_width=True, key="add_cust")
    _search_and_filter("cust")

    if _selected_rows("tbl_cust"):
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(CUSTOMERS, key="tbl_cust")
        with col_dr:
            rows = sel.selection.rows
            if rows:
                name = CUSTOMERS.iloc[rows[0]]["Наименование"]
                detail = DRAWER_DETAILS["customer"].get(name)
                st.markdown(f"### {name}")
                st.caption(detail["meta"] if detail else "Заказчик")
                st.button("✏ Редактировать", key="edit_cust")
                st.button("⏸ Деактивировать", key="deact_cust")
                st.divider()
                st.markdown("**АТРИБУТЫ**")
                if detail:
                    _drawer_fields(detail["fields"])
                else:
                    row = CUSTOMERS.iloc[rows[0]]
                    _drawer_fields({
                        "Наименование": name,
                        "Адрес": row["Адрес"],
                        "Контакт": row["Контакт"],
                    })
    else:
        _table(CUSTOMERS, key="tbl_cust")
