"""
SCR-002 — Дашборд директора
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_002_dashboard_director.py
"""
import datetime

import streamlit as st

st.set_page_config(
    page_title="SCR-002 — Дашборд директора (демо)",
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
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

TODAY = datetime.date(2026, 5, 24)

CRITICAL_STOCK = [
    {"type": "Сырьё", "name": "Сахар-песок", "quantity": "12 кг", "threshold": 50, "severity": "danger"},
    {"type": "Упаковка", "name": "Стакан 200 мл с крышкой", "quantity": "340 шт", "threshold": 500, "severity": "warn"},
    {"type": "Продукция", "name": "Кефир 1% 1л", "quantity": "86 шт", "threshold": 100, "severity": "warn"},
]

ACTIVE_RESERVES = [
    {"product": "Молоко 3,2%", "batch": "П-26-04-18", "order": "24-0117", "qty": 480, "date": "14.05"},
    {"product": "Кефир 1%", "batch": "П-26-04-22", "order": "24-0117", "qty": 240, "date": "14.05"},
    {"product": "Сметана 20% 200г", "batch": "П-26-05-02", "order": "24-0117", "qty": 246, "date": "14.05"},
    {"product": "Йогурт 0,9л", "batch": "П-26-05-05", "order": "24-0119", "qty": 60, "date": "15.05"},
]

OVERDUE_TASKS = [
    {
        "product": "Кефир 1% 1л",
        "quantity": "30 кор.",
        "status": "В работе",
        "executor": "Иванов Д.К.",
        "code": "T-26-0075",
        "overdue_days": 1,
    },
    {
        "product": "Йогурт «Питьевой» 0,9л",
        "quantity": "20 кор.",
        "status": "Остановлена",
        "executor": "Иванов Д.К.",
        "code": "T-26-0080",
        "overdue_days": 2,
    },
]

UPCOMING_DELIVERIES = [
    {"customer": "Магнит, Авиаторов", "date": "14.05", "courier": "Сидоров А.П.", "status": "Готов"},
    {"customer": "Пятёрочка, Калинина", "date": "14.05", "courier": "Петров К.С.", "status": "В пути"},
    {"customer": "ИП Морозова Л.К.", "date": "14.05", "courier": "Петров К.С.", "status": "Готов"},
    {"customer": "Магнит, Северный", "date": "15.05", "courier": "Петров К.С.", "status": "У водителя"},
    {"customer": "Лента, Взлётка", "date": "15.05", "courier": "Сидоров А.П.", "status": "Ожидает"},
]

TASKS_FOR_REVIEW = [
    {"product": "Молоко 3,2% 1л", "quantity": "40 кор.", "executor": "Сидоров А.П.", "code": "T-26-0078", "completed_at": "14.05 · 09:14"},
    {"product": "Сметана 20% 200г", "quantity": "25 кор.", "executor": "Сидоров А.П.", "code": "T-26-0076", "completed_at": "13.05 · 18:30"},
    {"product": "Кефир 1% 1л", "quantity": "20 кор.", "executor": "Иванов Д.К.", "code": "T-26-0074", "completed_at": "13.05 · 16:45"},
    {"product": "Сахар 0.5кг", "quantity": "50 кор.", "executor": "Сидоров А.П.", "code": "T-26-0072", "completed_at": "13.05 · 14:20"},
]

NOTIFICATIONS = [
    {"time": "09:14", "text": "Задача T-26-0078 завершена. Сидоров А.П. сдал отчёт."},
    {"time": "08:30", "text": "Заказ № 24-0121 переведён в доставку. Курьер Петров К.С."},
    {"time": "13.05", "text": 'Сырьё «Сахар-песок» опустилось ниже критического порога (12 кг).'},
    {"time": "13.05", "text": 'Задача T-26-0080 остановлена. Причина: «Поломка фасовщика».'},
    {"time": "12.05", "text": "Заказ № 24-0119 создан. Заказчик: ИП Соколова О.В."},
    {"time": "12.05", "text": "Задача T-26-0076 завершена. Сидоров А.П. — брак 2,1%."},
]


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

col_title, col_date = st.columns([3, 1])
col_title.markdown("## Дашборд")
col_date.caption(f"Сегодня, {TODAY.strftime('%d.%m.%Y')} · {TODAY.strftime('%A')}")


# ---------------------------------------------------------------------------
# Row 1: Критические остатки + Активные резервы
# ---------------------------------------------------------------------------

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Критические остатки**")
    if not CRITICAL_STOCK:
        st.success("Все остатки в норме")
    else:
        st.caption(f"{len(CRITICAL_STOCK)} позиции")
        for item in CRITICAL_STOCK:
            icon = "🔴" if item["severity"] == "danger" else "🟡"
            st.markdown(
                f"{icon} **{item['name']}** — {item['quantity']} "
                f"*(порог {item['threshold']}, {item['type'].lower()})*"
            )

with c2:
    st.markdown("**Активные резервы**")
    if not ACTIVE_RESERVES:
        st.success("Активных резервов нет")
    else:
        for r in ACTIVE_RESERVES[:3]:
            st.markdown(
                f"- **{r['product']}** — {r['qty']} шт "
                f"*(партия {r['batch']}, заказ {r['order']}, {r['date']})*"
            )
        if len(ACTIVE_RESERVES) > 3:
            st.caption(f"+ {len(ACTIVE_RESERVES) - 3} ещё")


# ---------------------------------------------------------------------------
# Row 2: Просроченные задачи + Ближайшие доставки
# ---------------------------------------------------------------------------

st.divider()
c3, c4 = st.columns(2)

with c3:
    st.markdown("**Просроченные задачи**")
    if not OVERDUE_TASKS:
        st.success("Все задачи в сроки")
    else:
        st.caption(f"{len(OVERDUE_TASKS)} задачи")
        for t in OVERDUE_TASKS:
            with st.container(border=True):
                st.markdown(f"**{t['product']}** · {t['quantity']}")
                st.caption(
                    f"{t['executor']} · {t['code']} · "
                    f"*{t['status']}* · "
                    f"🔴 Просрочена на {t['overdue_days']} дн."
                )

with c4:
    st.markdown("**Ближайшие доставки**")
    if not UPCOMING_DELIVERIES:
        st.success("Ближайших доставок нет")
    else:
        st.caption(f"{len(UPCOMING_DELIVERIES)} доставок · сегодня и завтра")
        for d in UPCOMING_DELIVERIES[:3]:
            status_icons = {"Готов": "⚪", "В пути": "🚛", "У водителя": "🔵", "Ожидает": "⏳"}
            icon = status_icons.get(d["status"], "")
            st.markdown(
                f"- {icon} **{d['customer']}** — {d['date']} · {d['courier']} · *{d['status']}*"
            )
        if len(UPCOMING_DELIVERIES) > 3:
            st.caption(f"+ {len(UPCOMING_DELIVERIES) - 3} ещё")


# ---------------------------------------------------------------------------
# Row 3: Задачи на проверку + Уведомления
# ---------------------------------------------------------------------------

st.divider()
c5, c6 = st.columns(2)

with c5:
    st.markdown("**Задачи на проверку**")
    if not TASKS_FOR_REVIEW:
        st.success("Все задачи закрыты")
    else:
        st.caption(f"{len(TASKS_FOR_REVIEW)} задачи · ждут закрытия")
        for t in TASKS_FOR_REVIEW[:3]:
            with st.container(border=True):
                st.markdown(f"**{t['product']}** · {t['quantity']}")
                st.caption(f"{t['executor']} · {t['code']} · завершена {t['completed_at']}")
        if len(TASKS_FOR_REVIEW) > 3:
            st.caption(f"+ {len(TASKS_FOR_REVIEW) - 3} ещё")

with c6:
    st.markdown("**Уведомления**")
    if not NOTIFICATIONS:
        st.info("Новых уведомлений нет")
    else:
        st.caption(f"{len(NOTIFICATIONS)} новых")
        for n in NOTIFICATIONS[:5]:
            st.markdown(f"**{n['time']}** — {n['text']}")
        if len(NOTIFICATIONS) > 5:
            st.caption(f"+ {len(NOTIFICATIONS) - 5} ещё")
