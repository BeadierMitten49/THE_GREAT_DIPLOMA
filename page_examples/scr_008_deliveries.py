"""
SCR-008 — Доставки
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_008_deliveries.py
"""
import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SCR-008 — Доставки (демо)",
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

TODAY = datetime.date(2026, 5, 24)

DELIVERIES = [
    {
        "id": 1,
        "order_id": 10,
        "order_number": "24-0117",
        "customer_name": "Магнит, ТТ Авиаторов",
        "delivery_address": "г. Красноярск, ул. Авиаторов, 25",
        "delivery_date": TODAY,
        "delivery_time": "до 11:00",
        "courier": "Сидоров А.П.",
        "status": "ready",
        "contact_note": "Звонить за час",
        "started_at": None,
        "delivered_at": None,
        "items": [
            {"product": "Сахар фасованный 0.5кг", "quantity": "40 кор."},
            {"product": "Мука пшеничная 1кг", "quantity": "12 кор."},
        ],
    },
    {
        "id": 2,
        "order_id": 11,
        "order_number": "24-0114",
        "customer_name": "Пятёрочка, ТТ Калинина",
        "delivery_address": "г. Красноярск, ул. Калинина, 64",
        "delivery_date": TODAY,
        "delivery_time": "до 13:00",
        "courier": "Петров К.С.",
        "status": "in_route",
        "contact_note": "Звонить за 15 мин",
        "started_at": "12:18",
        "delivered_at": None,
        "items": [
            {"product": "Молоко 3,2% 1л", "quantity": "30 кор."},
            {"product": "Кефир 1% 1л", "quantity": "15 кор. + 4 шт"},
        ],
    },
    {
        "id": 3,
        "order_id": 12,
        "order_number": "24-0119",
        "customer_name": "ИП Соколова О.В.",
        "delivery_address": "г. Красноярск, ул. Бограда, 14",
        "delivery_date": TODAY,
        "delivery_time": "до 15:00",
        "courier": "Петров К.С.",
        "status": "at_courier",
        "contact_note": "",
        "started_at": None,
        "delivered_at": None,
        "items": [
            {"product": "Сахар фасованный 0.5кг", "quantity": "10 кор."},
        ],
    },
    {
        "id": 4,
        "order_id": 13,
        "order_number": "24-0121",
        "customer_name": "Магнит, ТТ Северный",
        "delivery_address": "г. Красноярск, ул. 9 Мая, 77",
        "delivery_date": TODAY,
        "delivery_time": "до 17:00",
        "courier": "Петров К.С.",
        "status": "at_courier",
        "contact_note": "",
        "started_at": None,
        "delivered_at": None,
        "items": [
            {"product": "Сахар фасованный 1кг", "quantity": "20 кор."},
            {"product": "Мука пшеничная 1кг", "quantity": "60 кор."},
        ],
    },
    {
        "id": 5,
        "order_id": 14,
        "order_number": "24-0123",
        "customer_name": 'ООО "Кафе-бар"',
        "delivery_address": "г. Красноярск, ул. Маркса, 102",
        "delivery_date": TODAY,
        "delivery_time": "до 18:00",
        "courier": "Петров К.С.",
        "status": "at_courier",
        "contact_note": "Вход со двора",
        "started_at": None,
        "delivered_at": None,
        "items": [
            {"product": "Молоко 3,2% 1л", "quantity": "20 кор."},
            {"product": "Сметана 20% 200г", "quantity": "8 кор."},
        ],
    },
    {
        "id": 6,
        "order_id": 15,
        "order_number": "24-0110",
        "customer_name": "ИП Морозов Д.К.",
        "delivery_address": "г. Красноярск, пр. Свободный, 92",
        "delivery_date": TODAY,
        "delivery_time": None,
        "courier": "Сидоров А.П.",
        "status": "delivered",
        "contact_note": "",
        "started_at": "09:45",
        "delivered_at": "10:22",
        "items": [
            {"product": "Сахар фасованный 0.5кг", "quantity": "20 кор."},
        ],
    },
]

STATUS_LABELS = {
    "ready": "Готов к выдаче",
    "at_courier": "У водителя",
    "in_route": "В пути",
    "delivered": "Доставлено",
    "cancelled": "Отменена",
}

STATUS_ICONS = {
    "ready": "⚪",
    "at_courier": "🔵",
    "in_route": "🚛",
    "delivered": "✅",
    "cancelled": "❌",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_df(deliveries: list[dict]) -> pd.DataFrame:
    rows = []
    for d in deliveries:
        rows.append({
            "Дата": d["delivery_date"].strftime("%d.%m"),
            "Время": d["delivery_time"] or "—",
            "Заказчик": d["customer_name"],
            "Адрес": d["delivery_address"],
            "Исполнитель": d["courier"],
            "Статус": f"{STATUS_ICONS.get(d['status'], '')} {STATUS_LABELS.get(d['status'], d['status'])}",
        })
    return pd.DataFrame(rows)


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


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------


@st.dialog("Подтверждение доставки")
def _confirm_delivered_dialog(delivery: dict):
    st.markdown(f"### Заказ {delivery['order_number']}")
    st.caption(f"Заказчик: {delivery['customer_name']}")
    st.caption(f"Адрес: {delivery['delivery_address']}")
    st.caption(f"Курьер: {delivery['courier']}")

    st.divider()
    st.markdown("**Состав:**")
    for item in delivery["items"]:
        st.write(f"- {item['product']} — {item['quantity']}")

    st.divider()
    if st.button("Подтвердить доставку", type="primary", use_container_width=True):
        st.success(f"Доставка {delivery['order_number']} отмечена как доставлена (демо)")
        st.balloons()


@st.dialog("Отмена доставки")
def _cancel_delivery_dialog(delivery: dict):
    st.markdown(f"### Отмена доставки — {delivery['order_number']}")
    st.caption(f"Заказчик: {delivery['customer_name']}")

    reason = st.text_area("Причина отмены", placeholder="Укажите причину отмены доставки...")

    st.divider()
    if st.button("Отменить доставку", type="primary", use_container_width=True):
        if not reason:
            st.error("Укажите причину отмены")
        else:
            st.warning(f"Доставка {delivery['order_number']} отменена: {reason} (демо)")


@st.dialog("Начать выезд")
def _start_route_dialog(deliveries_batch: list[dict]):
    st.markdown(f"### Начать выезд ({len(deliveries_batch)} доставок)")

    for d in deliveries_batch:
        st.write(f"- **{d['order_number']}** — {d['customer_name']} ({d['delivery_time'] or 'без времени'})")

    st.divider()
    st.caption(f"Курьер: {deliveries_batch[0]['courier']}")

    if st.button("Начать выезд", type="primary", use_container_width=True):
        st.success(f"Выезд начат для {len(deliveries_batch)} доставок (демо)")
        st.balloons()


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown("## Доставки")
st.caption("Управление доставками — план на день, статусы, маршруты")


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

c1, c2, c3 = st.columns([1, 1, 1])
date_filter = c1.date_input(
    "Дата",
    value=TODAY,
    label_visibility="collapsed",
    key="filter_date",
)
status_filter = c2.selectbox(
    "Статус",
    options=["Все активные", "Готов к выдаче", "У водителя", "В пути", "Доставлено"],
    label_visibility="collapsed",
    key="filter_status",
)
courier_filter = c3.selectbox(
    "Исполнитель",
    options=["Любой", "Петров К.С.", "Сидоров А.П."],
    label_visibility="collapsed",
    key="filter_courier",
)

# Apply filters
filtered = DELIVERIES.copy()
if date_filter:
    filtered = [d for d in filtered if d["delivery_date"] == date_filter]

STATUS_MAP = {
    "Готов к выдаче": "ready",
    "У водителя": "at_courier",
    "В пути": "in_route",
    "Доставлено": "delivered",
}
if status_filter == "Все активные":
    filtered = [d for d in filtered if d["status"] != "cancelled"]
elif status_filter in STATUS_MAP:
    filtered = [d for d in filtered if d["status"] == STATUS_MAP[status_filter]]

if courier_filter != "Любой":
    filtered = [d for d in filtered if d["courier"] == courier_filter]


# ---------------------------------------------------------------------------
# Bulk actions — multiselect for "at_courier" deliveries
# ---------------------------------------------------------------------------

at_courier = [d for d in filtered if d["status"] == "at_courier"]
if at_courier:
    with st.expander(f"Групповой выезд ({len(at_courier)} доставок «У водителя»)", expanded=False):
        # Group by courier
        couriers = sorted(set(d["courier"] for d in at_courier))
        for courier in couriers:
            courier_deliveries = [d for d in at_courier if d["courier"] == courier]
            st.markdown(f"**{courier}** — {len(courier_deliveries)} доставок")
            selected_ids = []
            for d in courier_deliveries:
                if st.checkbox(
                    f"{d['order_number']} — {d['customer_name']} ({d['delivery_time'] or 'б/в'})",
                    key=f"bulk_{d['id']}",
                    value=True,
                ):
                    selected_ids.append(d["id"])

            if selected_ids:
                batch = [d for d in courier_deliveries if d["id"] in selected_ids]
                if st.button(
                    f"Начать выезд ({len(batch)} шт)",
                    key=f"bulk_start_{courier}",
                    type="primary",
                ):
                    _start_route_dialog(batch)
        st.divider()


# ---------------------------------------------------------------------------
# Table + Drawer
# ---------------------------------------------------------------------------

df = _to_df(filtered)

if df.empty:
    st.info("Нет доставок по выбранным фильтрам.")
elif _selected_rows("tbl_deliveries"):
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_deliveries")
    with col_dr:
        rows = sel.selection.rows
        if rows and rows[0] < len(filtered):
            delivery = filtered[rows[0]]

            # ---- Header ----
            st.markdown(f"### Заказ {delivery['order_number']}")
            status_label = STATUS_LABELS.get(delivery["status"], delivery["status"])
            status_icon = STATUS_ICONS.get(delivery["status"], "")
            st.caption(
                f"{status_icon} {status_label}  ·  "
                f"{delivery['delivery_date'].strftime('%d.%m.%Y')}  ·  "
                f"{delivery['delivery_time'] or '—'}  ·  "
                f"Курьер {delivery['courier']}"
            )

            # ---- Actions ----
            if delivery["status"] == "in_route":
                a1, a2 = st.columns(2)
                if a1.button("Доставлено", type="primary", use_container_width=True, key="dr_delivered"):
                    _confirm_delivered_dialog(delivery)
                if a2.button("Отмена доставки", use_container_width=True, key="dr_cancel"):
                    _cancel_delivery_dialog(delivery)
            elif delivery["status"] == "at_courier":
                a1, a2 = st.columns(2)
                if a1.button("Начать выезд", type="primary", use_container_width=True, key="dr_start"):
                    _start_route_dialog([delivery])
                if a2.button("Отмена доставки", use_container_width=True, key="dr_cancel_ac"):
                    _cancel_delivery_dialog(delivery)
            elif delivery["status"] == "ready":
                st.info("Ожидает выдачи на складе (страница «Отгрузки / Сборка»)")
            elif delivery["status"] == "delivered":
                st.success(f"Доставлено в {delivery['delivered_at']}")

            st.divider()

            # ---- Section: Заказчик ----
            st.markdown("**ЗАКАЗЧИК**")
            _drawer_fields({
                "Наименование": delivery["customer_name"],
                "Адрес": delivery["delivery_address"],
            })
            if delivery["contact_note"]:
                _drawer_fields({"Контакт": delivery["contact_note"]})

            st.divider()

            # ---- Section: Состав заказа ----
            st.markdown("**СОСТАВ ЗАКАЗА**")
            for item in delivery["items"]:
                st.write(f"- {item['product']} — {item['quantity']}")

            st.divider()

            # ---- Section: Доставка ----
            st.markdown("**ДОСТАВКА**")
            delivery_fields = {
                "Курьер": delivery["courier"],
                "Дата плановая": delivery["delivery_date"].strftime("%d.%m.%Y"),
                "Время начала выезда": delivery["started_at"] or "—",
                "Время доставки": delivery["delivered_at"] or "—",
            }
            _drawer_fields(delivery_fields)
else:
    _table(df, key="tbl_deliveries")


# ---------------------------------------------------------------------------
# Summary bar
# ---------------------------------------------------------------------------

total = len(filtered)
in_route = sum(1 for d in filtered if d["status"] == "in_route")
at_courier_count = sum(1 for d in filtered if d["status"] == "at_courier")
delivered_count = sum(1 for d in filtered if d["status"] == "delivered")
ready_count = sum(1 for d in filtered if d["status"] == "ready")

parts = [f"Всего: **{total}**"]
if ready_count:
    parts.append(f"Готовы к выдаче: **{ready_count}**")
if at_courier_count:
    parts.append(f"У водителя: **{at_courier_count}**")
if in_route:
    parts.append(f"В пути: **{in_route}**")
if delivered_count:
    parts.append(f"Доставлено: **{delivered_count}**")

st.caption("   ·   ".join(parts))
