import datetime
from decimal import Decimal

import pandas as pd
import streamlit as st

from api_client import APIError, get_client

TODAY = datetime.date.today()

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
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


# ── Load reference data ───────────────────────────────────────────────────────

try:
    raw_materials_list = client.get("/references/raw-materials", include_inactive=False)
    rm_full = {rm["id"]: rm for rm in raw_materials_list}
    packaging_list = client.get("/references/packaging", include_inactive=False)
    pkg_full = {p["id"]: p for p in packaging_list}
    products_list = client.get("/references/products", include_inactive=False)
    prod_full = {p["id"]: p for p in products_list}
except APIError as e:
    _err(e)
    rm_full = {}
    pkg_full = {}
    prod_full = {}


# ── Signal helpers ────────────────────────────────────────────────────────────


def _parse_date(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s)


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
    if sig in ("warn14", "warn30"):
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
    val = f"{float(avail):g} {unit}"
    if sig == "crit":
        return f"{val} ⬇ ниже крит."
    return val


# ── UI helpers ────────────────────────────────────────────────────────────────


def _table(df: pd.DataFrame, key: str):
    return st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )


def _selected_rows(key: str) -> list[int]:
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


# ── Filter / count ────────────────────────────────────────────────────────────

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
        rows.append({
            "Наименование":  b["Наименование"],
            "Кол-во":        f"{float(b['qty']):g} {b['unit']}",
            "Поступило":     b["received"].strftime("%d.%m.%Y"),
            "Срок годности": _expires_label(b),
            "Сигнал":        _signal_label(b),
            "Крит.":         f"{float(b['critical']):g} {b['unit']}",
            "Резерв":        f"{float(b['reserved']):g}" if b["reserved"] else "0",
            "Доступно":      _avail_label(b),
            "Комментарий":   b["comment"],
        })
    return pd.DataFrame(rows)


# ── Dialogs ───────────────────────────────────────────────────────────────────


@st.dialog("Приход сырья")
def _income_dialog():
    if not rm_full:
        st.info("Сначала добавьте сырьё в справочник.")
        return
    rm_ids = list(rm_full.keys())
    rm_id = st.selectbox(
        "Сырьё", options=rm_ids,
        format_func=lambda x: f"{rm_full[x]['name']} ({rm_full[x]['unit']})",
    )
    quantity = st.number_input("Количество", min_value=0.001, step=0.001, value=1.0)
    arrival_date = st.date_input("Дата прихода", value=TODAY)
    expiry_date = st.date_input("Срок годности до", value=TODAY)
    comment = st.text_input("Комментарий")
    if st.button("Оприходовать", type="primary", use_container_width=True):
        try:
            client.post(
                "/warehouse/raw-material-stock",
                body={
                    "raw_material_id": rm_id,
                    "quantity": float(quantity),
                    "arrival_date": str(arrival_date),
                    "expiry_date": str(expiry_date),
                    "comment": comment if comment else None,
                },
            )
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Списание")
def _writeoff_dialog(batch: dict):
    avail = float(batch["qty"] - batch["reserved"])
    st.write(f"**{batch['Наименование']}**")
    st.caption(
        f"Поступление {batch['received'].strftime('%d.%m.%Y')} "
        f"· Доступно: {avail:g} {batch['unit']}"
    )
    amount = st.number_input(
        "Количество к списанию",
        min_value=0.001,
        max_value=max(float(batch["qty"]), 0.001),
        step=0.001,
        value=0.001,
    )
    if st.button("Списать", type="primary", use_container_width=True):
        try:
            client.post(
                f"/warehouse/raw-material-stock/{batch['id']}/write-off",
                body={"amount": float(amount)},
            )
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Корректировка")
def _adjust_dialog(batch: dict):
    st.write(f"**{batch['Наименование']}**")
    st.caption(
        f"Поступление {batch['received'].strftime('%d.%m.%Y')} "
        f"· Текущее кол-во: {float(batch['qty']):g} {batch['unit']}"
    )
    new_qty = st.number_input(
        "Новое количество", min_value=0.0, step=0.001, value=float(batch["qty"]),
    )
    new_comment = st.text_input("Комментарий", value=batch["comment"] or "")
    if st.button("Сохранить", type="primary", use_container_width=True):
        try:
            client.patch(
                f"/warehouse/raw-material-stock/{batch['id']}",
                body={
                    "quantity": float(new_qty),
                    "comment": new_comment if new_comment else None,
                },
            )
            st.rerun()
        except APIError as e:
            _err(e)


# ── Packaging helpers ─────────────────────────────────────────────────────────


def _pkg_signal(row: dict) -> str:
    if row["qty"] < row["critical"]:
        return "crit"
    return "ok"


def _pkg_signal_label(row: dict) -> str:
    if _pkg_signal(row) == "crit":
        return "🔴 Ниже крит."
    return ""


def _pkg_qty_label(row: dict) -> str:
    val = f"{row['qty']} {row['unit']}"
    if _pkg_signal(row) == "crit":
        return f"{val} ⬇ ниже крит."
    return val


PKG_SIGNAL_MAP = {"Все": None, "Ниже критического": "crit"}


def _pkg_filter(items: list[dict], search: str, signal: str | None) -> list[dict]:
    result = items
    if search:
        result = [b for b in result if search.lower() in b["Наименование"].lower()]
    if signal:
        result = [b for b in result if _pkg_signal(b) == signal]
    return result


def _pkg_to_df(items: list[dict]) -> pd.DataFrame:
    rows = []
    for b in items:
        rows.append({
            "Наименование":  b["Наименование"],
            "Кол-во":        f"{b['qty']} {b['unit']}",
            "Крит. остаток": f"{b['critical']} {b['unit']}",
            "Сигнал":        _pkg_signal_label(b),
            "Остаток":       _pkg_qty_label(b),
            "Комментарий":   b["comment"],
        })
    return pd.DataFrame(rows)


def _pkg_search_and_signal(key: str):
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


# ── Packaging dialogs ────────────────────────────────────────────────────────


@st.dialog("Приход упаковки")
def _pkg_income_dialog():
    if not pkg_full:
        st.info("Сначала добавьте упаковку в справочник.")
        return
    pkg_ids = list(pkg_full.keys())
    pkg_id = st.selectbox(
        "Упаковка", options=pkg_ids,
        format_func=lambda x: f"{pkg_full[x]['name']} ({pkg_full[x]['unit']})",
    )
    quantity = st.number_input("Количество", min_value=1, value=1)
    comment = st.text_input("Комментарий")
    if st.button("Оприходовать", type="primary", use_container_width=True):
        try:
            client.post(
                "/warehouse/packaging-stock",
                body={
                    "packaging_id": pkg_id,
                    "quantity": quantity,
                    "comment": comment if comment else None,
                },
            )
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Списание упаковки")
def _pkg_writeoff_dialog(item: dict):
    st.write(f"**{item['Наименование']}**")
    st.caption(f"На складе: {item['qty']} {item['unit']}")
    amount = st.number_input(
        "Количество к списанию",
        min_value=1,
        max_value=max(item["qty"], 1),
        value=1,
    )
    if st.button("Списать", type="primary", use_container_width=True):
        try:
            client.post(
                f"/warehouse/packaging-stock/{item['id']}/write-off",
                body={"amount": amount},
            )
            st.rerun()
        except APIError as e:
            _err(e)


# ── Product helpers ──────────────────────────────────────────────────────────


def _prod_batch_label(row: dict) -> str:
    return f"П-{row['batch_year']}-{row['batch_number']:03d}"


def _prod_qty_parts(row: dict) -> tuple[int, int]:
    per_box = row["per_box"]
    if per_box <= 0:
        return 0, row["qty"]
    return row["qty"] // per_box, row["qty"] % per_box


def _prod_signal(row: dict) -> str:
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


def _prod_signal_label(row: dict) -> str:
    sig = _prod_signal(row)
    days = _days_left(row["expires"])
    if sig == "expired":
        return f"⛔ Истекло {row['expires'].strftime('%d.%m')}"
    if sig == "crit":
        return "🔴 Ниже крит."
    if sig in ("warn14", "warn30"):
        return f"⚠ через {days} дн."
    return ""


def _prod_expires_label(row: dict) -> str:
    sig = _prod_signal(row)
    days = _days_left(row["expires"])
    exp_str = row["expires"].strftime("%d.%m.%Y")
    if sig == "expired":
        return f"Истекло {row['expires'].strftime('%d.%m')}"
    if sig in ("warn14", "warn30"):
        return f"{exp_str} (через {days} дн.)"
    return exp_str


def _prod_avail_label(row: dict) -> str:
    avail = row["qty"] - row["reserved"]
    if _prod_signal(row) == "crit":
        return f"{avail} ниже крит."
    return str(avail)


def _prod_reserved_label(row: dict) -> str:
    if not row["reserved"]:
        return "0"
    orders = row.get("reserved_orders", [])
    if orders:
        return f"{row['reserved']} → № {', '.join(str(o) for o in orders)}"
    return str(row["reserved"])


PROD_SIGNAL_MAP = {
    "Все": None,
    "Ниже критического": "crit",
    "Истекло": "expired",
    "Истекает ≤14 дн": "warn14",
    "Истекает ≤30 дн": "warn30",
}


def _prod_filter(batches: list[dict], search: str, signal: str | None) -> list[dict]:
    result = batches
    if search:
        q = search.lower()
        result = [
            b for b in result
            if q in b["Наименование"].lower() or q in _prod_batch_label(b).lower()
        ]
    if signal:
        result = [b for b in result if _prod_signal(b) == signal]
    return result


def _prod_count_signals(batches: list[dict]) -> dict:
    counts = {"crit": 0, "expired": 0, "warn14": 0, "reserved": 0}
    for b in batches:
        s = _prod_signal(b)
        if s in counts:
            counts[s] += 1
        if b["reserved"] > 0:
            counts["reserved"] += 1
    return counts


def _prod_to_df(batches: list[dict]) -> pd.DataFrame:
    rows = []
    for b in batches:
        boxes, loose = _prod_qty_parts(b)
        rows.append({
            "Продукт":        b["Наименование"],
            "№ партии":       _prod_batch_label(b),
            "Кол-во":         f"{boxes} / {loose}  ({b['qty']} шт)",
            "Поступило":      b["received"].strftime("%d.%m.%Y"),
            "Срок годности":  _prod_expires_label(b),
            "Крит.":          str(b["critical"]),
            "Резерв":         _prod_reserved_label(b),
            "Доступно":       _prod_avail_label(b),
            "Сигнал":         _prod_signal_label(b),
        })
    return pd.DataFrame(rows)


def _prod_search_and_signal(key: str):
    c1, c2 = st.columns([3, 1])
    c1.text_input(
        "Поиск", placeholder="Поиск по продукту или № партии",
        label_visibility="collapsed", key=f"search_{key}",
    )
    c2.selectbox(
        "Сигнал",
        list(PROD_SIGNAL_MAP.keys()),
        label_visibility="collapsed", key=f"signal_{key}",
    )


# ── Product dialogs ─────────────────────────────────────────────────────────


@st.dialog("Приёмка по задаче")
def _prod_accept_task_dialog(completed_tasks: list[dict]):
    if not completed_tasks:
        st.info("Нет завершённых задач для приёмки.")
        return
    task_options = {
        t["task_id"]: (
            f"#{t['task_id']} — {t['product_name']} "
            f"· план {t['planned_quantity']} / факт {t['actual_quantity']} шт"
        )
        for t in completed_tasks
    }
    task_id = st.selectbox(
        "Задача", options=list(task_options.keys()),
        format_func=lambda x: task_options[x],
    )
    selected = next(t for t in completed_tasks if t["task_id"] == task_id)
    st.caption(f"Продукт: **{selected['product_name']}**")
    st.caption(
        f"Плановое кол-во: {selected['planned_quantity']} шт · "
        f"Фактическое кол-во: **{selected['actual_quantity']} шт**"
    )
    if selected.get("completed_at"):
        st.caption(f"Завершена: {selected['completed_at'][:10]}")
    if st.button("Принять на склад", type="primary", use_container_width=True):
        try:
            client.post(
                "/warehouse/product-stock/from-task",
                body={"task_id": task_id},
            )
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Списание продукции")
def _prod_writeoff_dialog(batch: dict):
    st.write(f"**{batch['Наименование']}**")
    st.caption(
        f"Партия {_prod_batch_label(batch)} · "
        f"На складе: {batch['qty']} шт"
    )
    amount = st.number_input(
        "Количество к списанию (шт.)",
        min_value=1,
        max_value=max(batch["qty"], 1),
        value=1,
    )
    if st.button("Списать", type="primary", use_container_width=True):
        try:
            client.post(
                f"/warehouse/product-stock/{batch['id']}/write-off",
                body={"amount": amount},
            )
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Корректировка продукции")
def _prod_adjust_dialog(batch: dict):
    st.write(f"**{batch['Наименование']}**")
    st.caption(
        f"Партия {_prod_batch_label(batch)} · "
        f"Текущее кол-во: {batch['qty']} шт"
    )
    new_qty = st.number_input(
        "Новое количество (шт.)", min_value=0, value=batch["qty"],
    )
    new_comment = st.text_input("Комментарий", value=batch["comment"] or "")
    if st.button("Сохранить", type="primary", use_container_width=True):
        try:
            client.patch(
                f"/warehouse/product-stock/{batch['id']}",
                body={
                    "quantity": new_qty,
                    "comment": new_comment if new_comment else None,
                },
            )
            st.rerun()
        except APIError as e:
            _err(e)


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Склад")

tab_raw, tab_pkg, tab_prod = st.tabs(["Сырьё", "Упаковка", "Продукция"])

# ── Сырьё ─────────────────────────────────────────────────────────────────────
with tab_raw:
    st.caption("Партии сырья на складе — остатки, резервы, сроки годности")

    try:
        raw_stocks = client.get("/warehouse/raw-material-stock")
    except APIError as e:
        _err(e)
        raw_stocks = []

    batches_raw: list[dict] = []
    for s in raw_stocks:
        rm = rm_full.get(s["raw_material_id"], {})
        batches_raw.append({
            "id": s["id"],
            "raw_material_id": s["raw_material_id"],
            "Наименование": rm.get("name", f"id={s['raw_material_id']}"),
            "qty": Decimal(str(s["quantity"])),
            "unit": rm.get("unit", ""),
            "received": _parse_date(s["arrival_date"]),
            "expires": _parse_date(s["expiry_date"]),
            "critical": Decimal(str(rm.get("critical_stock", 0))),
            "reserved": Decimal(str(s.get("reserved", 0))),
            "comment": s.get("comment") or "",
        })

    # pre-read filter state (from previous render)
    search_val = st.session_state.get("search_raw", "")
    signal_val = st.session_state.get("signal_raw", "Все")
    signal_filter = SIGNAL_MAP.get(signal_val)
    filtered = _filter_batches(batches_raw, search_val, signal_filter)

    sel_rows = _selected_rows("tbl_raw")
    sel_batch = (
        filtered[sel_rows[0]]
        if sel_rows and sel_rows[0] < len(filtered)
        else None
    )

    # ---- action buttons ----
    c_btn = st.columns([3, 1, 1, 1])
    if c_btn[1].button("+ Приход", type="primary", use_container_width=True):
        _income_dialog()
    if c_btn[2].button("− Списание", use_container_width=True, disabled=sel_batch is None):
        if sel_batch is not None:
            _writeoff_dialog(sel_batch)
    if c_btn[3].button("✎ Коррект.", use_container_width=True, disabled=sel_batch is None):
        if sel_batch is not None:
            _adjust_dialog(sel_batch)

    # ---- search + signal filter ----
    _search_and_signal("raw")

    total = len(batches_raw)
    total_counts = _count_signals(batches_raw)
    df = _to_df(filtered)

    # ---- table + drawer ----
    if df.empty:
        st.info("Нет позиций по заданным фильтрам.")
    elif sel_rows:
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(df, key="tbl_raw")
        with col_dr:
            rows = sel.selection.rows
            if rows and rows[0] < len(filtered):
                batch = filtered[rows[0]]
                avail = batch["qty"] - batch["reserved"]

                st.markdown(f"### {batch['Наименование']}")
                st.caption(f"Партия · Поступление {batch['received'].strftime('%d.%m.%Y')}")
                dr_c1, dr_c2 = st.columns(2)
                if dr_c1.button("− Списание", key="dr_writeoff"):
                    _writeoff_dialog(batch)
                if dr_c2.button("✎ Корректировка", key="dr_adjust"):
                    _adjust_dialog(batch)
                st.divider()
                st.markdown("**ОСТАТКИ**")
                _drawer_fields({
                    "Кол-во":              f"{float(batch['qty']):g} {batch['unit']}",
                    "Резерв":              f"{float(batch['reserved']):g} {batch['unit']}",
                    "Доступно":            f"{float(avail):g} {batch['unit']}",
                    "Критический остаток": f"{float(batch['critical']):g} {batch['unit']}",
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

    # ---- summary bar ----
    shown = len(filtered)
    if signal_filter or search_val:
        found_str = f"Найдено: **{shown}** из {total} позиций"
    else:
        found_str = f"Всего позиций: **{total}**"
    sc = total_counts
    st.caption(
        f"{found_str}   ·   "
        f"Критических: **{sc['crit']}**   ·   "
        f"Истекло: **{sc['expired']}**   ·   "
        f"Истекает ≤14 дн: **{sc['warn14']}**   ·   "
        f"Истекает ≤30 дн: **{sc['warn30']}**"
    )

# ── Упаковка ──────────────────────────────────────────────────────────────────
with tab_pkg:
    st.caption("Остатки упаковочных материалов")

    try:
        pkg_stocks = client.get("/warehouse/packaging-stock")
    except APIError as e:
        _err(e)
        pkg_stocks = []

    items_pkg: list[dict] = []
    for s in pkg_stocks:
        pk = pkg_full.get(s["packaging_id"], {})
        items_pkg.append({
            "id": s["id"],
            "packaging_id": s["packaging_id"],
            "Наименование": pk.get("name", f"id={s['packaging_id']}"),
            "qty": s["quantity"],
            "unit": pk.get("unit", ""),
            "critical": pk.get("critical_stock", 0),
            "comment": s.get("comment") or "",
        })

    pkg_search = st.session_state.get("search_pkg", "")
    pkg_sig_val = st.session_state.get("signal_pkg", "Все")
    pkg_sig_filter = PKG_SIGNAL_MAP.get(pkg_sig_val)
    pkg_filtered = _pkg_filter(items_pkg, pkg_search, pkg_sig_filter)

    pkg_sel_rows = _selected_rows("tbl_pkg")
    pkg_sel = (
        pkg_filtered[pkg_sel_rows[0]]
        if pkg_sel_rows and pkg_sel_rows[0] < len(pkg_filtered)
        else None
    )

    # ---- action buttons ----
    pc = st.columns([4, 1, 1])
    if pc[1].button("+ Приход", type="primary", use_container_width=True, key="pkg_btn_income"):
        _pkg_income_dialog()
    if pc[2].button("− Списание", use_container_width=True, key="pkg_btn_wo", disabled=pkg_sel is None):
        if pkg_sel is not None:
            _pkg_writeoff_dialog(pkg_sel)

    # ---- search + signal filter ----
    _pkg_search_and_signal("pkg")

    pkg_total = len(items_pkg)
    pkg_crit_count = sum(1 for b in items_pkg if _pkg_signal(b) == "crit")
    pkg_df = _pkg_to_df(pkg_filtered)

    # ---- table + drawer ----
    if pkg_df.empty:
        st.info("Нет позиций по заданным фильтрам.")
    elif pkg_sel_rows:
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(pkg_df, key="tbl_pkg")
        with col_dr:
            rows = sel.selection.rows
            if rows and rows[0] < len(pkg_filtered):
                item = pkg_filtered[rows[0]]
                st.markdown(f"### {item['Наименование']}")
                if st.button("− Списание", key="pkg_dr_writeoff"):
                    _pkg_writeoff_dialog(item)
                st.divider()
                st.markdown("**ОСТАТКИ**")
                _drawer_fields({
                    "Кол-во":              f"{item['qty']} {item['unit']}",
                    "Критический остаток": f"{item['critical']} {item['unit']}",
                    "Сигнал":              _pkg_signal_label(item) or "—",
                })
                if item["comment"]:
                    st.divider()
                    st.markdown("**КОММЕНТАРИЙ**")
                    st.write(item["comment"])
    else:
        _table(pkg_df, key="tbl_pkg")

    # ---- summary bar ----
    pkg_shown = len(pkg_filtered)
    if pkg_sig_filter or pkg_search:
        pkg_found_str = f"Найдено: **{pkg_shown}** из {pkg_total} позиций"
    else:
        pkg_found_str = f"Всего позиций: **{pkg_total}**"
    st.caption(f"{pkg_found_str}   ·   Ниже критического: **{pkg_crit_count}**")

# ── Продукция ─────────────────────────────────────────────────────────────────
with tab_prod:
    st.caption("Партии готовой продукции — остатки, резервы, сроки годности")

    try:
        prod_stocks = client.get("/warehouse/product-stock")
    except APIError as e:
        _err(e)
        prod_stocks = []

    batches_prod: list[dict] = []
    for s in prod_stocks:
        pr = prod_full.get(s["product_id"], {})
        batches_prod.append({
            "id": s["id"],
            "product_id": s["product_id"],
            "Наименование": pr.get("name", f"id={s['product_id']}"),
            "qty": s["quantity"],
            "per_box": pr.get("units_per_box", 1),
            "received": _parse_date(s["arrival_date"]),
            "expires": _parse_date(s["expiry_date"]),
            "critical": pr.get("critical_stock", 0),
            "reserved": s.get("reserved", 0),
            "reserved_orders": s.get("reserved_orders", []),
            "batch_number": s["batch_number"],
            "batch_year": s["batch_year"],
            "comment": s.get("comment") or "",
        })

    # ---- completed tasks for acceptance ----
    try:
        completed_tasks = client.get("/warehouse/product-stock/pending-tasks")
    except APIError:
        completed_tasks = []
    pending_count = len(completed_tasks)

    prod_search = st.session_state.get("search_prod", "")
    prod_sig_val = st.session_state.get("signal_prod", "Все")
    prod_sig_filter = PROD_SIGNAL_MAP.get(prod_sig_val)
    prod_filtered = _prod_filter(batches_prod, prod_search, prod_sig_filter)

    prod_sel_rows = _selected_rows("tbl_prod")
    prod_sel = (
        prod_filtered[prod_sel_rows[0]]
        if prod_sel_rows and prod_sel_rows[0] < len(prod_filtered)
        else None
    )

    # ---- action buttons ----
    prc = st.columns([3, 1, 1, 1])
    accept_label = f"Приёмка ({pending_count})" if pending_count else "Приёмка"
    if prc[1].button(accept_label, type="primary", use_container_width=True, key="prod_btn_income", disabled=pending_count == 0):
        _prod_accept_task_dialog(completed_tasks)
    if prc[2].button("− Списание", use_container_width=True, key="prod_btn_wo", disabled=prod_sel is None):
        if prod_sel is not None:
            _prod_writeoff_dialog(prod_sel)
    if prc[3].button("✎ Коррект.", use_container_width=True, key="prod_btn_adj", disabled=prod_sel is None):
        if prod_sel is not None:
            _prod_adjust_dialog(prod_sel)

    # ---- search + signal filter ----
    _prod_search_and_signal("prod")

    prod_total = len(batches_prod)
    prod_counts = _prod_count_signals(batches_prod)
    prod_df = _prod_to_df(prod_filtered)

    # ---- table + drawer ----
    if prod_df.empty:
        st.info("Нет позиций по заданным фильтрам.")
    elif prod_sel_rows:
        col_tbl, col_dr = st.columns([3, 2])
        with col_tbl:
            sel = _table(prod_df, key="tbl_prod")
        with col_dr:
            rows = sel.selection.rows
            if rows and rows[0] < len(prod_filtered):
                batch = prod_filtered[rows[0]]
                avail = batch["qty"] - batch["reserved"]
                boxes, loose = _prod_qty_parts(batch)

                st.markdown(f"### {batch['Наименование']}")
                st.caption(
                    f"Партия {_prod_batch_label(batch)} · "
                    f"Поступление {batch['received'].strftime('%d.%m.%Y')}"
                )
                dr_c1, dr_c2 = st.columns(2)
                if dr_c1.button("− Списание", key="prod_dr_writeoff"):
                    _prod_writeoff_dialog(batch)
                if dr_c2.button("✎ Корректировка", key="prod_dr_adjust"):
                    _prod_adjust_dialog(batch)
                st.divider()
                st.markdown("**ОСТАТКИ**")
                _drawer_fields({
                    "Кол-во":              f"{boxes} кор. / {loose} шт  ({batch['qty']} шт)",
                    "Резерв":              f"{batch['reserved']} шт",
                    "Доступно":            f"{avail} шт",
                    "Критический остаток":  f"{batch['critical']} шт",
                })
                if batch.get("reserved_orders"):
                    st.divider()
                    st.markdown("**РЕЗЕРВЫ ПО ЗАКАЗАМ**")
                    for oid in batch["reserved_orders"]:
                        st.write(f"→ Заказ #{oid}")
                st.divider()
                st.markdown("**СРОК ГОДНОСТИ**")
                _drawer_fields({
                    "Поступило": batch["received"].strftime("%d.%m.%Y"),
                    "Истекает":  batch["expires"].strftime("%d.%m.%Y"),
                    "Сигнал":    _prod_signal_label(batch) or "—",
                })
                if batch["comment"]:
                    st.divider()
                    st.markdown("**КОММЕНТАРИЙ**")
                    st.write(batch["comment"])
    else:
        _table(prod_df, key="tbl_prod")

    # ---- summary bar ----
    prod_shown = len(prod_filtered)
    if prod_sig_filter or prod_search:
        prod_found_str = f"Найдено: **{prod_shown}** из {prod_total} партий"
    else:
        prod_found_str = f"Всего партий: **{prod_total}**"
    sc = prod_counts
    st.caption(
        f"{prod_found_str}   ·   "
        f"Под резерв: **{sc['reserved']}**   ·   "
        f"Критических: **{sc['crit']}**   ·   "
        f"Истекает ≤14 дн: **{sc['warn14']}**"
    )
