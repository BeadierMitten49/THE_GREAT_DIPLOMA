"""
SCR-011 — Склад упаковки
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_011_warehouse_packaging.py
"""

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SCR-011 — Склад упаковки (демо)",
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

ITEMS = [
    {
        "Наименование": "Стакан 200 мл",
        "qty": 1200, "unit": "шт",
        "critical": 500,
        "comment": "",
    },
    {
        "Наименование": "Стакан 400 мл",
        "qty": 80, "unit": "шт",
        "critical": 200,
        "comment": "Заказ у поставщика",
    },
    {
        "Наименование": "Крышка для стакана 200 мл",
        "qty": 3500, "unit": "шт",
        "critical": 500,
        "comment": "",
    },
    {
        "Наименование": "Крышка для стакана 400 мл",
        "qty": 150, "unit": "шт",
        "critical": 200,
        "comment": "",
    },
    {
        "Наименование": "Этикетка «Кефир 1%»",
        "qty": 600, "unit": "шт",
        "critical": 300,
        "comment": "",
    },
    {
        "Наименование": "Этикетка «Сметана 20%»",
        "qty": 40, "unit": "шт",
        "critical": 300,
        "comment": "Тираж в печати",
    },
    {
        "Наименование": "Коробка гофро 400×300×200",
        "qty": 250, "unit": "шт",
        "critical": 100,
        "comment": "",
    },
    {
        "Наименование": "Плёнка термоусадочная",
        "qty": 18, "unit": "рул",
        "critical": 5,
        "comment": "",
    },
]


# ---------------------------------------------------------------------------
# Helpers — сигналы
# ---------------------------------------------------------------------------

def _signal(row: dict) -> str:
    if row["qty"] < row["critical"]:
        return "crit"
    return "ok"


def _signal_label(row: dict) -> str:
    if _signal(row) == "crit":
        return "🔴 Ниже крит."
    return ""


def _qty_label(row: dict) -> str:
    sig = _signal(row)
    val = f"{row['qty']:g} {row['unit']}"
    if sig == "crit":
        return f"{val} ⬇ ниже крит."
    return val


# ---------------------------------------------------------------------------
# Helpers — UI
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


def _search_and_signal(key: str):
    c1, c2 = st.columns([3, 1])
    c1.text_input(
        "Поиск", placeholder="Поиск по наименованию",
        label_visibility="collapsed", key=f"search_{key}",
    )
    c2.selectbox(
        "Сигнал",
        ["Все", "Ниже критического"],
        label_visibility="collapsed", key=f"signal_{key}",
    )


# ---------------------------------------------------------------------------
# Фильтрация
# ---------------------------------------------------------------------------

SIGNAL_MAP = {
    "Все": None,
    "Ниже критического": "crit",
}


def _filter_items(items: list[dict], search: str, signal: str | None) -> list[dict]:
    result = items
    if search:
        result = [b for b in result if search.lower() in b["Наименование"].lower()]
    if signal:
        result = [b for b in result if _signal(b) == signal]
    return result


def _count_signals(items: list[dict]) -> int:
    return sum(1 for b in items if _signal(b) == "crit")


def _to_df(items: list[dict]) -> pd.DataFrame:
    rows = []
    for b in items:
        rows.append({
            "Наименование":  b["Наименование"],
            "Кол-во":        f"{b['qty']:g} {b['unit']}",
            "Крит. остаток":  f"{b['critical']:g} {b['unit']}",
            "Сигнал":        _signal_label(b),
            "Остаток":       _qty_label(b),
            "Комментарий":   b["comment"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Шапка
# ---------------------------------------------------------------------------

st.markdown("## Склад упаковки")
st.caption("Остатки упаковочных материалов")

# ---------------------------------------------------------------------------
# Кнопки действий + фильтры
# ---------------------------------------------------------------------------

c_btn = st.columns([4, 1, 1])
c_btn[1].button("+ Приход", type="primary", use_container_width=True, key="btn_income")
c_btn[2].button("− Списание", use_container_width=True, key="btn_writeoff")

_search_and_signal("pkg")

search_val = st.session_state.get("search_pkg", "")
signal_val = st.session_state.get("signal_pkg", "Все")
signal_filter = SIGNAL_MAP[signal_val]

filtered = _filter_items(ITEMS, search_val, signal_filter)
total = len(ITEMS)
crit_count = _count_signals(ITEMS)

# ---------------------------------------------------------------------------
# Таблица + drawer
# ---------------------------------------------------------------------------

df = _to_df(filtered)

if df.empty:
    st.info("Нет позиций по заданным фильтрам.")
elif _selected_rows("tbl_pkg"):
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_pkg")
    with col_dr:
        rows = sel.selection.rows
        if rows:
            idx = rows[0]
            item = filtered[idx]
            sig = _signal(item)

            st.markdown(f"### {item['Наименование']}")
            st.button("− Списание", key="dr_writeoff")
            st.divider()
            st.markdown("**ОСТАТКИ**")
            _drawer_fields({
                "Кол-во":              f"{item['qty']:g} {item['unit']}",
                "Критический остаток": f"{item['critical']:g} {item['unit']}",
                "Сигнал":              _signal_label(item) or "—",
            })
            if item["comment"]:
                st.divider()
                st.markdown("**КОММЕНТАРИЙ**")
                st.write(item["comment"])
else:
    _table(df, key="tbl_pkg")

# ---------------------------------------------------------------------------
# Summary bar
# ---------------------------------------------------------------------------

shown = len(filtered)
if signal_filter or search_val:
    found_str = f"Найдено: **{shown}** из {total} позиций"
else:
    found_str = f"Всего позиций: **{total}**"

st.caption(f"{found_str}   ·   Ниже критического: **{crit_count}**")
