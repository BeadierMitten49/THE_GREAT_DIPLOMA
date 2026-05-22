"""
SCR-012 — Склад готовой продукции
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_012_warehouse_product.py
"""
import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SCR-012 — Склад готовой продукции (демо)",
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

BATCHES = [
    {
        "product": "Молоко 3,2% 1 л",
        "qty": 480, "per_box": 12,
        "batch_year": 2026, "batch_number": 1,
        "received": datetime.date(2026, 4, 18),
        "expires":  datetime.date(2026, 6, 2),    # через 11 дн — warn ≤14
        "critical": 100,
        "reserved": 480,
        "orders": ["24-0117"],
        "comment": "",
    },
    {
        "product": "Молоко 3,2% 1 л",
        "qty": 720, "per_box": 12,
        "batch_year": 2026, "batch_number": 2,
        "received": datetime.date(2026, 5, 8),
        "expires":  datetime.date(2026, 6, 15),
        "critical": 100,
        "reserved": 0,
        "orders": [],
        "comment": "",
    },
    {
        "product": "Кефир 1% 1 л",
        "qty": 244, "per_box": 12,
        "batch_year": 2026, "batch_number": 3,
        "received": datetime.date(2026, 4, 22),
        "expires":  datetime.date(2026, 5, 19),    # истекло
        "critical": 100,
        "reserved": 184,
        "orders": ["24-0114", "24-0117"],
        "comment": "",
    },
    {
        "product": "Кефир 1% 1 л",
        "qty": 86, "per_box": 12,
        "batch_year": 2026, "batch_number": 4,
        "received": datetime.date(2026, 5, 12),
        "expires":  datetime.date(2026, 6, 19),
        "critical": 100,
        "reserved": 0,
        "orders": [],
        "comment": "",
    },
    {
        "product": "Сметана 20% 200 г",
        "qty": 306, "per_box": 12,
        "batch_year": 2026, "batch_number": 5,
        "received": datetime.date(2026, 5, 2),
        "expires":  datetime.date(2026, 5, 31),    # через 9 дн — warn ≤14
        "critical": 50,
        "reserved": 246,
        "orders": ["24-0115", "24-0117"],
        "comment": "",
    },
    {
        "product": "Творог 9%",
        "qty": 216, "per_box": 12,
        "batch_year": 2026, "batch_number": 6,
        "received": datetime.date(2026, 5, 9),
        "expires":  datetime.date(2026, 5, 23),    # через 1 дн — warn ≤14
        "critical": 40,
        "reserved": 60,
        "orders": ["24-0118"],
        "comment": "",
    },
    {
        "product": "Йогурт «Питьевой» клубника 0,9 л",
        "qty": 180, "per_box": 12,
        "batch_year": 2026, "batch_number": 7,
        "received": datetime.date(2026, 5, 5),
        "expires":  datetime.date(2026, 5, 25),    # через 3 дн — warn ≤14
        "critical": 60,
        "reserved": 60,
        "orders": ["24-0119"],
        "comment": "",
    },
]


# ---------------------------------------------------------------------------
# Helpers — batch number
# ---------------------------------------------------------------------------

def _batch_label(row: dict) -> str:
    return f"П-{row['batch_year']}-{row['batch_number']:03d}"


# ---------------------------------------------------------------------------
# Helpers — quantity format (boxes / loose)
# ---------------------------------------------------------------------------

def _qty_parts(row: dict) -> tuple[int, int]:
    """Return (boxes, loose) from total quantity."""
    boxes = row["qty"] // row["per_box"]
    loose = row["qty"] % row["per_box"]
    return boxes, loose


def _qty_label(row: dict) -> str:
    boxes, loose = _qty_parts(row)
    return f"{boxes} / {loose}"


def _qty_total(row: dict) -> str:
    return f"{row['qty']} шт"


# ---------------------------------------------------------------------------
# Helpers — signals
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
    sig = _signal(row)
    if sig == "crit":
        return f"{avail} ниже крит."
    return str(avail)


def _reserved_label(row: dict) -> str:
    if not row["reserved"]:
        return "0"
    parts = [str(row["reserved"])]
    if row["orders"]:
        parts.append("→ № " + ", ".join(row["orders"]))
    return "\n".join(parts)


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
        "Поиск", placeholder="Поиск по продукту или № партии",
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
        q = search.lower()
        result = [
            b for b in result
            if q in b["product"].lower() or q in _batch_label(b).lower()
        ]
    if signal:
        result = [b for b in result if _signal(b) == signal]
    return result


def _count_signals(batches: list[dict]) -> dict:
    counts = {"crit": 0, "expired": 0, "warn14": 0, "reserved": 0}
    for b in batches:
        s = _signal(b)
        if s in counts:
            counts[s] += 1
        if b["reserved"] > 0:
            counts["reserved"] += 1
    return counts


def _to_df(batches: list[dict]) -> pd.DataFrame:
    rows = []
    for b in batches:
        avail = b["qty"] - b["reserved"]
        rows.append({
            "Продукт":        b["product"],
            "№ партии":       _batch_label(b),
            "Кол-во":         f"{_qty_label(b)}  ({_qty_total(b)})",
            "Поступило":      b["received"].strftime("%d.%m.%Y"),
            "Срок годности":  _expires_label(b),
            "Крит.":          str(b["critical"]),
            "Резерв":         _reserved_label(b),
            "Доступно":       _avail_label(b),
            "Сигнал":         _signal_label(b),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Шапка
# ---------------------------------------------------------------------------

st.markdown("## Склад готовой продукции")
st.caption("Партии готовой продукции — остатки, резервы, сроки годности")

# ---------------------------------------------------------------------------
# Кнопки действий + фильтры
# ---------------------------------------------------------------------------

c_btn = st.columns([3, 1, 1, 1])
c_btn[1].button("+ Приёмка", type="primary", use_container_width=True, key="btn_income")
c_btn[2].button("− Списание", use_container_width=True, key="btn_writeoff")
c_btn[3].button("✎ Коррект.", use_container_width=True, key="btn_adjust")

_search_and_signal("prod")

search_val = st.session_state.get("search_prod", "")
signal_val = st.session_state.get("signal_prod", "Все")
signal_filter = SIGNAL_MAP[signal_val]

filtered = _filter_batches(BATCHES, search_val, signal_filter)
total = len(BATCHES)
total_counts = _count_signals(BATCHES)

# ---------------------------------------------------------------------------
# Таблица + drawer
# ---------------------------------------------------------------------------

df = _to_df(filtered)

if df.empty:
    st.info("Нет позиций по заданным фильтрам.")
elif _selected_rows("tbl_prod"):
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_prod")
    with col_dr:
        rows = sel.selection.rows
        if rows:
            idx = rows[0]
            batch = filtered[idx]
            sig = _signal(batch)
            avail = batch["qty"] - batch["reserved"]
            boxes, loose = _qty_parts(batch)

            st.markdown(f"### {batch['product']}")
            st.caption(f"Партия {_batch_label(batch)} · Поступление {batch['received'].strftime('%d.%m.%Y')}")
            st.button("− Списание", key="dr_writeoff")
            st.button("✎ Корректировка", key="dr_adjust")
            st.divider()
            st.markdown("**ОСТАТКИ**")
            _drawer_fields({
                "Кол-во":              f"{boxes} кор. / {loose} шт  ({batch['qty']} шт)",
                "Резерв":              f"{batch['reserved']} шт",
                "Доступно":            f"{avail} шт",
                "Критический остаток":  f"{batch['critical']} шт",
            })
            if batch["orders"]:
                st.divider()
                st.markdown("**РЕЗЕРВЫ ПО ЗАКАЗАМ**")
                for order in batch["orders"]:
                    st.write(f"→ № {order}")
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
    _table(df, key="tbl_prod")

# ---------------------------------------------------------------------------
# Summary bar
# ---------------------------------------------------------------------------

shown = len(filtered)
if signal_filter or search_val:
    found_str = f"Найдено: **{shown}** из {total} партий"
else:
    found_str = f"Всего партий: **{total}**"

s = total_counts
st.caption(
    f"{found_str}   ·   "
    f"Под резерв: **{s['reserved']}**   ·   "
    f"Критических: **{s['crit']}**   ·   "
    f"Истекает ≤14 дн: **{s['warn14']}**"
)
