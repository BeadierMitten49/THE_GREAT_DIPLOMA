"""
SCR-006 — Заказы
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_006_orders.py
"""
import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SCR-006 — Заказы (демо)",
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

STATUS_OPTIONS = ["Все", "Создан", "Производство", "Сборка", "Доставка", "Завершён"]

STATUS_EMOJI = {
    "Создан": "⚪",
    "Производство": "🔵",
    "Сборка": "🟡",
    "Доставка": "🟢",
    "Завершён": "✅",
}

ORDERS = [
    {
        "id": 1,
        "number": "24-0117",
        "customer_name": "Магнит, ТТ Авиаторов",
        "customer_address": "г. Красноярск, ул. Авиаторов, 25",
        "customer_comment": "Звонить за час до доставки",
        "delivery_date": datetime.date(2026, 5, 14),
        "created_at": datetime.date(2026, 5, 12),
        "status": "Сборка",
        "items": [
            {"product": "Молоко 3,2% 1л", "qty_boxes": 40, "qty_loose": 0, "reservation": "П-2026-001 · 480 шт зарезервировано"},
            {"product": "Кефир 1% 1л", "qty_boxes": 20, "qty_loose": 0, "reservation": "П-2026-003 · 240 шт зарезервировано"},
            {"product": "Сметана 20% 200г", "qty_boxes": 10, "qty_loose": 0, "reservation": "П-2026-005 · 240 шт зарезервировано"},
        ],
        "tasks": [],
        "courier": "Сидоров А.П.",
        "delivery_time": None,
    },
    {
        "id": 2,
        "number": "24-0118",
        "customer_name": "Пятёрочка, ТТ Свободный",
        "customer_address": "г. Красноярск, пр. Свободный, 64",
        "customer_comment": "",
        "delivery_date": datetime.date(2026, 5, 15),
        "created_at": datetime.date(2026, 5, 13),
        "status": "Производство",
        "items": [
            {"product": "Молоко 3,2% 1л", "qty_boxes": 40, "qty_loose": 0, "reservation": None},
            {"product": "Йогурт «Питьевой» клубника 0,9л", "qty_boxes": 20, "qty_loose": 0, "reservation": None},
        ],
        "tasks": [
            {"task_number": "T-26-0079", "product": "Молоко 3,2%", "qty": "40 кор.", "executor": "Сидоров А.П.", "deadline": "14.05.2026", "status": "В работе"},
            {"task_number": "T-26-0080", "product": "Йогурт клубника 0,9л", "qty": "20 кор.", "executor": "Иванов Д.К.", "deadline": "14.05.2026", "status": "Создана"},
        ],
        "courier": None,
        "delivery_time": None,
    },
    {
        "id": 3,
        "number": "24-0119",
        "customer_name": "ИП Соколова О.В.",
        "customer_address": "г. Красноярск, ул. Маерчака, 12",
        "customer_comment": "Только после 14:00",
        "delivery_date": datetime.date(2026, 5, 16),
        "created_at": datetime.date(2026, 5, 13),
        "status": "Создан",
        "items": [
            {"product": "Сметана 20% 200г", "qty_boxes": 5, "qty_loose": 6, "reservation": None},
            {"product": "Творог 9%", "qty_boxes": 8, "qty_loose": 0, "reservation": None},
        ],
        "tasks": [],
        "courier": None,
        "delivery_time": None,
    },
    {
        "id": 4,
        "number": "24-0120",
        "customer_name": "Магнит, ТТ Северный",
        "customer_address": "г. Красноярск, ул. 9 Мая, 77",
        "customer_comment": "",
        "delivery_date": datetime.date(2026, 5, 16),
        "created_at": datetime.date(2026, 5, 14),
        "status": "Производство",
        "items": [
            {"product": "Молоко 3,2% 1л", "qty_boxes": 30, "qty_loose": 0, "reservation": None},
            {"product": "Кефир 1% 1л", "qty_boxes": 15, "qty_loose": 0, "reservation": None},
        ],
        "tasks": [
            {"task_number": "T-26-0081", "product": "Молоко 3,2%", "qty": "30 кор.", "executor": "Петров К.Н.", "deadline": "15.05.2026", "status": "В работе"},
        ],
        "courier": None,
        "delivery_time": None,
    },
    {
        "id": 5,
        "number": "24-0121",
        "customer_name": "Лента, ТТ Взлётка",
        "customer_address": "г. Красноярск, ул. Молокова, 54",
        "customer_comment": "",
        "delivery_date": datetime.date(2026, 5, 17),
        "created_at": datetime.date(2026, 5, 14),
        "status": "Доставка",
        "items": [
            {"product": "Молоко 3,2% 1л", "qty_boxes": 60, "qty_loose": 0, "reservation": "П-2026-002 · 720 шт зарезервировано"},
            {"product": "Сметана 20% 200г", "qty_boxes": 25, "qty_loose": 0, "reservation": "П-2026-005 · 600 шт зарезервировано"},
        ],
        "tasks": [],
        "courier": "Козлов Д.В.",
        "delivery_time": "09:30",
    },
    {
        "id": 6,
        "number": "24-0122",
        "customer_name": "ИП Гаврилов А.С.",
        "customer_address": "г. Красноярск, ул. Ленина, 101",
        "customer_comment": "",
        "delivery_date": datetime.date(2026, 5, 18),
        "created_at": datetime.date(2026, 5, 15),
        "status": "Создан",
        "items": [
            {"product": "Кефир 1% 1л", "qty_boxes": 10, "qty_loose": 0, "reservation": None},
        ],
        "tasks": [],
        "courier": None,
        "delivery_time": None,
    },
    {
        "id": 7,
        "number": "24-0123",
        "customer_name": "Пятёрочка, ТТ Семафорная",
        "customer_address": "г. Красноярск, ул. Семафорная, 189",
        "customer_comment": "",
        "delivery_date": datetime.date(2026, 5, 19),
        "created_at": datetime.date(2026, 5, 15),
        "status": "Производство",
        "items": [
            {"product": "Молоко 3,2% 1л", "qty_boxes": 50, "qty_loose": 0, "reservation": None},
            {"product": "Кефир 1% 1л", "qty_boxes": 30, "qty_loose": 0, "reservation": None},
            {"product": "Йогурт «Питьевой» клубника 0,9л", "qty_boxes": 15, "qty_loose": 0, "reservation": None},
        ],
        "tasks": [
            {"task_number": "T-26-0082", "product": "Молоко 3,2%", "qty": "50 кор.", "executor": "Сидоров А.П.", "deadline": "18.05.2026", "status": "Создана"},
        ],
        "courier": None,
        "delivery_time": None,
    },
    {
        "id": 8,
        "number": "24-0124",
        "customer_name": "Магнит, ТТ Партизана Железняка",
        "customer_address": "г. Красноярск, ул. Партизана Железняка, 40",
        "customer_comment": "Заезд со двора",
        "delivery_date": datetime.date(2026, 5, 20),
        "created_at": datetime.date(2026, 5, 16),
        "status": "Создан",
        "items": [
            {"product": "Молоко 3,2% 1л", "qty_boxes": 35, "qty_loose": 0, "reservation": None},
            {"product": "Сметана 20% 200г", "qty_boxes": 20, "qty_loose": 0, "reservation": None},
        ],
        "tasks": [],
        "courier": None,
        "delivery_time": None,
    },
    {
        "id": 9,
        "number": "24-0125",
        "customer_name": "ООО «Кафе-бар»",
        "customer_address": "г. Красноярск, ул. Мира, 88",
        "customer_comment": "Рампа #2",
        "delivery_date": datetime.date(2026, 5, 21),
        "created_at": datetime.date(2026, 5, 16),
        "status": "Создан",
        "items": [
            {"product": "Творог 9%", "qty_boxes": 12, "qty_loose": 0, "reservation": None},
            {"product": "Сметана 20% 200г", "qty_boxes": 8, "qty_loose": 6, "reservation": None},
        ],
        "tasks": [],
        "courier": None,
        "delivery_time": None,
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item_qty_label(item: dict) -> str:
    if item["qty_loose"]:
        return f"{item['qty_boxes']} кор. / {item['qty_loose']} шт"
    return f"{item['qty_boxes']} кор."


def _status_counts(orders: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for o in orders:
        counts[o["status"]] = counts.get(o["status"], 0) + 1
    return counts


def _filter_orders(orders: list[dict], status: str, date_from: datetime.date | None, date_to: datetime.date | None) -> list[dict]:
    result = orders
    if status != "Все":
        result = [o for o in result if o["status"] == status]
    if date_from:
        result = [o for o in result if o["delivery_date"] >= date_from]
    if date_to:
        result = [o for o in result if o["delivery_date"] <= date_to]
    return result


def _to_df(orders: list[dict]) -> pd.DataFrame:
    rows = []
    for o in orders:
        rows.append({
            "№": o["number"],
            "Заказчик": o["customer_name"],
            "Дата доставки": o["delivery_date"].strftime("%d.%m.%Y"),
            "Статус": f"{STATUS_EMOJI.get(o['status'], '')} {o['status']}",
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

@st.dialog("Создать заказ")
def _create_order_dialog():
    st.text_input("Заказчик", placeholder="Название / ИП / ООО")
    st.text_input("Адрес доставки")
    st.date_input("Дата доставки", value=TODAY + datetime.timedelta(days=3))
    st.text_area("Комментарий", placeholder="Необязательно")
    st.divider()
    st.caption("Состав заказа добавляется после создания")
    if st.button("Создать", type="primary", use_container_width=True):
        st.success("Заказ создан (демо)")
        st.rerun()


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown("## Заказы")

h1, h2 = st.columns([4, 1])
h2.button("+ Создать заказ", type="primary", use_container_width=True, key="btn_create", on_click=lambda: None)

if st.session_state.get("btn_create"):
    _create_order_dialog()

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

c1, c2, c3 = st.columns([1, 1, 1])
status_filter = c1.selectbox("Статус", STATUS_OPTIONS, key="filter_status", label_visibility="collapsed")
date_from = c2.date_input("Дата доставки от", value=None, key="filter_date_from", format="DD.MM.YYYY")
date_to = c3.date_input("Дата доставки до", value=None, key="filter_date_to", format="DD.MM.YYYY")

filtered = _filter_orders(ORDERS, status_filter, date_from, date_to)
status_counts = _status_counts(ORDERS)

# ---------------------------------------------------------------------------
# Table + Drawer
# ---------------------------------------------------------------------------

df = _to_df(filtered)

if df.empty:
    st.info("Нет заказов по выбранным фильтрам.")
elif _selected_rows("tbl_orders"):
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_orders")
    with col_dr:
        rows = sel.selection.rows
        if rows:
            idx = rows[0]
            order = filtered[idx]

            # Header
            st.markdown(f"### Заказ {order['customer_name'].split(',')[0]}")
            st.caption(
                f"{STATUS_EMOJI.get(order['status'], '')} {order['status']}  ·  "
                f"Создан {order['created_at'].strftime('%d.%m.%Y')}  ·  "
                f"Доставка {order['delivery_date'].strftime('%d.%m.%Y')}"
            )

            # Actions
            bc1, bc2, bc3 = st.columns(3)
            bc1.button("✎ Редактировать", key="dr_edit")
            if order["status"] == "Производство":
                bc2.button("→ В сборку", type="primary", key="dr_to_assembly")
            bc3.button("🗑 Удалить", key="dr_delete")

            st.divider()

            # Section: Заказчик
            st.markdown("**ЗАКАЗЧИК**")
            _drawer_fields({
                "Наименование": order["customer_name"],
                "Адрес": order["customer_address"],
            })
            if order["customer_comment"]:
                _drawer_fields({"Комментарий": order["customer_comment"]})

            st.divider()

            # Section: Состав заказа
            st.markdown("**СОСТАВ ЗАКАЗА**")
            for item in order["items"]:
                st.write(f"**{item['product']}** — {_item_qty_label(item)}")
                if item["reservation"]:
                    st.caption(f"└ {item['reservation']}")
                elif order["status"] == "Производство":
                    task_ref = next(
                        (t for t in order["tasks"] if item["product"].startswith(t["product"].split(" ")[0])),
                        None,
                    )
                    if task_ref:
                        st.caption(f"└ ⚠ Резерв ещё не создан — задача {task_ref['task_number']} в работе")
                    else:
                        st.caption("└ ⚠ Резерв ещё не создан")

            # Section: Производственные задачи (if any)
            if order["tasks"]:
                st.divider()
                st.markdown("**ПРОИЗВОДСТВЕННЫЕ ЗАДАЧИ**")
                for task in order["tasks"]:
                    with st.container(border=True):
                        st.write(f"**{task['product']}** · {task['qty']} · {task['task_number']}")
                        tc1, tc2 = st.columns([3, 1])
                        tc1.caption(f"{task['executor']} · до {task['deadline']}")
                        tc2.write(f"{task['status']}")

            st.divider()

            # Section: Доставка
            st.markdown("**ДОСТАВКА**")
            _drawer_fields({
                "Курьер": order["courier"] or "не назначен",
                "Дата плановая": order["delivery_date"].strftime("%d.%m.%Y"),
                "Время начала": order["delivery_time"] or "—",
            })
else:
    _table(df, key="tbl_orders")

# ---------------------------------------------------------------------------
# Summary bar
# ---------------------------------------------------------------------------

total = len(ORDERS)
shown = len(filtered)
if status_filter != "Все" or date_from or date_to:
    found_str = f"Найдено: **{shown}** из {total} заказов"
else:
    found_str = f"Всего заказов: **{total}**"

parts = [found_str]
for s_name in ["Создан", "Производство", "Сборка", "Доставка"]:
    cnt = status_counts.get(s_name, 0)
    if cnt:
        parts.append(f"{STATUS_EMOJI.get(s_name, '')} {s_name}: **{cnt}**")

st.caption("   ·   ".join(parts))
