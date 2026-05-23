"""
SCR-010 — Склад сырья
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_010_warehouse_raw.py
"""
import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SCR-010 — Склад сырья (демо)",
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

TODAY = datetime.date(2026, 5, 22)

BATCHES_RAW = [
    {
        "Наименование": "Молоко цельное",
        "qty": 80, "unit": "кг",
        "received": datetime.date(2026, 4, 15),
        "expires":  datetime.date(2026, 5, 12),   # истекло
        "critical": 100, "reserved": 0,
        "comment": "К утилизации",
    },
    {
        "Наименование": "Молоко цельное",
        "qty": 240, "unit": "кг",
        "received": datetime.date(2026, 4, 18),
        "expires":  datetime.date(2026, 6, 2),    # через 11 дн — warn ≤14
        "critical": 100, "reserved": 180,
        "comment": "",
    },
    {
        "Наименование": "Сахар-песок",
        "qty": 12, "unit": "кг",
        "received": datetime.date(2026, 5, 2),
        "expires":  datetime.date(2026, 6, 2),    # ниже критического
        "critical": 50, "reserved": 0,
        "comment": "",
    },
    {
        "Наименование": "Стабилизатор «Юнипектин»",
        "qty": 5, "unit": "кг",
        "received": datetime.date(2026, 5, 10),
        "expires":  datetime.date(2026, 11, 10),
        "critical": 1, "reserved": 0.8,
        "comment": "",
    },
    {
        "Наименование": "Закваска кефирная",
        "qty": 8, "unit": "кг",
        "received": datetime.date(2026, 4, 22),
        "expires":  datetime.date(2026, 6, 13),   # через 22 дн — warn ≤30
        "critical": 2, "reserved": 0.3,
        "comment": "2 партии в работе",
    },
    {
        "Наименование": "Соль пищевая",
        "qty": 85, "unit": "кг",
        "received": datetime.date(2026, 5, 5),
        "expires":  datetime.date(2028, 5, 5),
        "critical": 10, "reserved": 0,
        "comment": "",
    },
    {
        "Наименование": "Молоко обезжиренное",
        "qty": 320, "unit": "кг",
        "received": datetime.date(2026, 5, 10),
        "expires":  datetime.date(2026, 5, 17),
        "critical": 100, "reserved": 60,
        "comment": "",
    },
    {
        "Наименование": "Сливки 33%",
        "qty": 42, "unit": "кг",
        "received": datetime.date(2026, 5, 12),
        "expires":  datetime.date(2026, 5, 19),
        "critical": 15, "reserved": 15,
        "comment": "",
    },
]


# ---------------------------------------------------------------------------
# Helpers — сигналы
# ---------------------------------------------------------------------------

def _days_left(exp_date: datetime.date) -> int:
    return (exp_date - TODAY).days


def _signal(row: dict) -> str:
    days = _days_left(row["expires"])
    if days < 0:
        return "expired"
    avail = row["qty"] - row["reserved"]
    if avail < row["critical"]:
        return "crit"
    if days <= 14:
        return "warn14"
    if days <= 30:
        return "warn30"
    return "ok"


def _signal_label(row: dict) -> str:
    sig = _signal(row)
    days = _days_left(row["expires"])
    if sig == "expired":
        return f"⛔ Истекло {row['expires'].strftime('%d.%m')}"
    if sig == "crit":
        return "🔴 Ниже крит."
    if sig == "warn14":
        return f"⚠ через {days} дн."
    if sig == "warn30":
        return f"⚠ через {days} дн."
    return ""


def _expires_label(row: dict) -> str:
    sig = _signal(row)
    days = _days_left(row["expires"])
    exp_str = row["expires"].strftime("%d.%m.%Y")
    if sig == "expired":
        return f"Истекло {row['expires'].strftime('%d.%m')}"
    if sig in ("warn14", "warn30"):
        return f"{exp_str} (через {days} дн.)"
    return exp_str


def _avail_label(row: dict) -> str:
    avail = row["qty"] - row["reserved"]
    unit = row["unit"]
    sig = _signal(row)
    val = f"{avail:g} {unit}"
    if sig == "crit":
        return f"{val} ⬇ ниже крит."
    return val


# ---------------------------------------------------------------------------
# Helpers — UI (по образцу scr_015_references.py)
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
        ["Все", "Ниже критического", "Истекло", "Истекает ≤14 дн", "Истекает ≤30 дн"],
        label_visibility="collapsed", key=f"signal_{key}",
    )


# ---------------------------------------------------------------------------
# Фильтрация
# ---------------------------------------------------------------------------

SIGNAL_MAP = {
    "Все": None,
    "Ниже критического": "crit",
    "Истекло": "expired",
    "Истекает ≤14 дн": "warn14",
    "Истекает ≤30 дн": "warn30",
}


def _filter_batches(batches: list[dict], search: str, signal: str | None) -> list[dict]:
    result = batches
    if search:
        result = [b for b in result if search.lower() in b["Наименование"].lower()]
    if signal:
        result = [b for b in result if _signal(b) == signal]
    return result


def _count_signals(batches: list[dict]) -> dict:
    counts = {"crit": 0, "expired": 0, "warn14": 0, "warn30": 0}
    for b in batches:
        s = _signal(b)
        if s in counts:
            counts[s] += 1
    return counts


def _to_df(batches: list[dict]) -> pd.DataFrame:
    rows = []
    for b in batches:
        avail = b["qty"] - b["reserved"]
        rows.append({
            "Наименование":  b["Наименование"],
            "Кол-во":        f"{b['qty']:g} {b['unit']}",
            "Поступило":     b["received"].strftime("%d.%m.%Y"),
            "Срок годности": _expires_label(b),
            "Сигнал":        _signal_label(b),
            "Крит.":         f"{b['critical']:g} {b['unit']}",
            "Резерв":        f"{b['reserved']:g}" if b["reserved"] else "0",
            "Доступно":      _avail_label(b),
            "Комментарий":   b["comment"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Шапка
# ---------------------------------------------------------------------------

st.markdown("## Склад сырья")
st.caption("Партии сырья на складе — остатки, резервы, сроки годности")

# ---------------------------------------------------------------------------
# Кнопки действий + фильтры
# ---------------------------------------------------------------------------

c_btn = st.columns([3, 1, 1, 1])
c_btn[1].button("+ Приход", type="primary", use_container_width=True, key="btn_income")
c_btn[2].button("− Списание", use_container_width=True, key="btn_writeoff")
c_btn[3].button("✎ Коррект.", use_container_width=True, key="btn_adjust")

_search_and_signal("raw")

search_val = st.session_state.get("search_raw", "")
signal_val = st.session_state.get("signal_raw", "Все")
signal_filter = SIGNAL_MAP[signal_val]

filtered = _filter_batches(BATCHES_RAW, search_val, signal_filter)
total = len(BATCHES_RAW)
total_counts = _count_signals(BATCHES_RAW)

# ---------------------------------------------------------------------------
# Таблица + drawer
# ---------------------------------------------------------------------------

df = _to_df(filtered)

if df.empty:
    st.info("Нет позиций по заданным фильтрам.")
elif _selected_rows("tbl_raw"):
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_raw")
    with col_dr:
        rows = sel.selection.rows
        if rows:
            idx = rows[0]
            batch = filtered[idx]
            sig = _signal(batch)
            avail = batch["qty"] - batch["reserved"]

            st.markdown(f"### {batch['Наименование']}")
            st.caption(f"Партия · Поступление {batch['received'].strftime('%d.%m.%Y')}")
            st.button("− Списание", key="dr_writeoff")
            st.button("✎ Корректировка", key="dr_adjust")
            st.divider()
            st.markdown("**ОСТАТКИ**")
            _drawer_fields({
                "Кол-во":            f"{batch['qty']:g} {batch['unit']}",
                "Резерв":            f"{batch['reserved']:g} {batch['unit']}",
                "Доступно":          f"{avail:g} {batch['unit']}",
                "Критический остаток": f"{batch['critical']:g} {batch['unit']}",
            })
            st.divider()
            st.markdown("**СРОК ГОДНОСТИ**")
            _drawer_fields({
                "Поступило": batch["received"].strftime("%d.%m.%Y"),
                "Истекает":  batch["expires"].strftime("%d.%m.%Y"),
                "Сигнал":    _signal_label(batch) or "—",
            })
            if batch["comment"]:
                st.divider()
                st.markdown("**КОММЕНТАРИЙ**")
                st.write(batch["comment"])
else:
    _table(df, key="tbl_raw")

# ---------------------------------------------------------------------------
# Summary bar
# ---------------------------------------------------------------------------

shown = len(filtered)
if signal_filter or search_val:
    found_str = f"Найдено: **{shown}** из {total} позиций"
else:
    found_str = f"Всего позиций: **{total}**"

s = total_counts
st.caption(
    f"{found_str}   ·   "
    f"Критических: **{s['crit']}**   ·   "
    f"Истекло: **{s['expired']}**   ·   "
    f"Истекает ≤14 дн: **{s['warn14']}**   ·   "
    f"Истекает ≤30 дн: **{s['warn30']}**"
)
