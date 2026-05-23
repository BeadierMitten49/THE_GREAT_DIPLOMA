"""
SCR-007 — Производственные задачи
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_007_tasks.py
"""
import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SCR-007 — Производственные задачи (демо)",
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

STATUS_OPTIONS = ["Все", "Создана", "В работе", "Остановлена", "Завершена", "Закрыта"]
STATUS_EMOJI = {
    "Создана": "⚪",
    "В работе": "🔵",
    "Остановлена": "🟠",
    "Завершена": "🟢",
    "Закрыта": "✅",
}

TYPE_LABELS = {
    "order_task": "Под заказ",
    "stock_task": "В запас",
}

EXECUTORS = {
    1: "Сидоров А.П.",
    2: "Иванов Д.К.",
    3: "Петров К.Н.",
}

PRODUCTS = {
    1: "Молоко 3,2% 1л",
    2: "Кефир 1% 1л",
    3: "Сметана 20% 200г",
    4: "Йогурт «Питьевой» клубника 0,9л",
    5: "Творог 9%",
}

RAW_MATERIALS = {
    1: "Молоко цельное коровье",
    2: "Закваска кефирная",
    3: "Сливки 35%",
    4: "Клубничный наполнитель",
    5: "Сычужный фермент",
}

TASKS = [
    {
        "id": 79,
        "product_id": 1,
        "quantity": 480,
        "executor_id": 1,
        "start_date": datetime.date(2026, 5, 13),
        "deadline": datetime.date(2026, 5, 14),
        "task_type": "order_task",
        "status": "В работе",
        "order_id": 118,
        "comment": None,
        "created_at": datetime.date(2026, 5, 13),
        "actual_start_at": datetime.datetime(2026, 5, 13, 8, 30),
        "actual_end_at": None,
        "raw_materials": [
            {"rm_id": 1, "planned_qty": 520.0, "reserved_qty": 520.0},
        ],
        "stops": [],
    },
    {
        "id": 80,
        "product_id": 4,
        "quantity": 240,
        "executor_id": 2,
        "start_date": datetime.date(2026, 5, 13),
        "deadline": datetime.date(2026, 5, 14),
        "task_type": "order_task",
        "status": "Создана",
        "order_id": 118,
        "comment": "Приоритет высокий",
        "created_at": datetime.date(2026, 5, 13),
        "actual_start_at": None,
        "actual_end_at": None,
        "raw_materials": [
            {"rm_id": 1, "planned_qty": 216.0, "reserved_qty": 216.0},
            {"rm_id": 4, "planned_qty": 48.0, "reserved_qty": 48.0},
        ],
        "stops": [],
    },
    {
        "id": 81,
        "product_id": 1,
        "quantity": 360,
        "executor_id": 3,
        "start_date": datetime.date(2026, 5, 14),
        "deadline": datetime.date(2026, 5, 15),
        "task_type": "order_task",
        "status": "В работе",
        "order_id": 120,
        "comment": None,
        "created_at": datetime.date(2026, 5, 14),
        "actual_start_at": datetime.datetime(2026, 5, 14, 7, 0),
        "actual_end_at": None,
        "raw_materials": [
            {"rm_id": 1, "planned_qty": 390.0, "reserved_qty": 390.0},
        ],
        "stops": [],
    },
    {
        "id": 82,
        "product_id": 2,
        "quantity": 600,
        "executor_id": 1,
        "start_date": datetime.date(2026, 5, 15),
        "deadline": datetime.date(2026, 5, 18),
        "task_type": "stock_task",
        "status": "Остановлена",
        "order_id": None,
        "comment": "Пополнение склада на неделю",
        "created_at": datetime.date(2026, 5, 15),
        "actual_start_at": datetime.datetime(2026, 5, 15, 8, 0),
        "actual_end_at": None,
        "raw_materials": [
            {"rm_id": 1, "planned_qty": 630.0, "reserved_qty": 630.0},
            {"rm_id": 2, "planned_qty": 12.0, "reserved_qty": 12.0},
        ],
        "stops": [
            {"reason": "Поломка транспортёра, ждём ремонт", "stopped_at": "15.05.2026 14:20", "resumed_at": None},
        ],
    },
    {
        "id": 83,
        "product_id": 3,
        "quantity": 480,
        "executor_id": 2,
        "start_date": datetime.date(2026, 5, 12),
        "deadline": datetime.date(2026, 5, 14),
        "task_type": "order_task",
        "status": "Завершена",
        "order_id": 117,
        "comment": None,
        "created_at": datetime.date(2026, 5, 12),
        "actual_start_at": datetime.datetime(2026, 5, 12, 9, 0),
        "actual_end_at": datetime.datetime(2026, 5, 13, 16, 45),
        "raw_materials": [
            {"rm_id": 3, "planned_qty": 96.0, "reserved_qty": 96.0},
        ],
        "stops": [],
        "completion": {"actual_quantity": 470, "comment": "10 шт брак при фасовке"},
    },
    {
        "id": 84,
        "product_id": 5,
        "quantity": 200,
        "executor_id": 3,
        "start_date": datetime.date(2026, 5, 10),
        "deadline": datetime.date(2026, 5, 12),
        "task_type": "stock_task",
        "status": "Закрыта",
        "order_id": None,
        "comment": None,
        "created_at": datetime.date(2026, 5, 10),
        "actual_start_at": datetime.datetime(2026, 5, 10, 7, 30),
        "actual_end_at": datetime.datetime(2026, 5, 11, 17, 0),
        "raw_materials": [
            {"rm_id": 1, "planned_qty": 300.0, "reserved_qty": 300.0},
            {"rm_id": 5, "planned_qty": 2.0, "reserved_qty": 2.0},
        ],
        "stops": [],
        "completion": {"actual_quantity": 200, "comment": None},
    },
    {
        "id": 85,
        "product_id": 1,
        "quantity": 720,
        "executor_id": 1,
        "start_date": datetime.date(2026, 5, 16),
        "deadline": datetime.date(2026, 5, 19),
        "task_type": "stock_task",
        "status": "Создана",
        "order_id": None,
        "comment": "Партия для следующей недели",
        "created_at": datetime.date(2026, 5, 16),
        "actual_start_at": None,
        "actual_end_at": None,
        "raw_materials": [
            {"rm_id": 1, "planned_qty": 780.0, "reserved_qty": 620.0},
        ],
        "stops": [],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task_number(task: dict) -> str:
    return f"T-{task['created_at'].year % 100}-{task['id']:04d}"


def _status_label(status: str) -> str:
    return f"{STATUS_EMOJI.get(status, '')} {status}"


def _to_df(tasks: list[dict]) -> pd.DataFrame:
    rows = []
    for t in tasks:
        rows.append({
            "№": _task_number(t),
            "Продукт": PRODUCTS.get(t["product_id"], "?"),
            "Кол-во": f"{t['quantity']} шт",
            "Исполнитель": EXECUTORS.get(t["executor_id"], "?"),
            "Дедлайн": t["deadline"].strftime("%d.%m.%Y"),
            "Тип": TYPE_LABELS.get(t["task_type"], t["task_type"]),
            "Статус": _status_label(t["status"]),
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


def _filter_tasks(tasks: list[dict], status: str, executor: str) -> list[dict]:
    result = tasks
    if status != "Все":
        result = [t for t in result if t["status"] == status]
    if executor != "Все":
        eid = next((k for k, v in EXECUTORS.items() if v == executor), None)
        if eid is not None:
            result = [t for t in result if t["executor_id"] == eid]
    return result


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Создать задачу")
def _create_task_dialog():
    prod_id = st.selectbox(
        "Продукт",
        options=list(PRODUCTS.keys()),
        format_func=lambda x: PRODUCTS[x],
    )
    quantity = st.number_input("Количество (шт.)", min_value=1, value=100)
    executor_id = st.selectbox(
        "Исполнитель",
        options=list(EXECUTORS.keys()),
        format_func=lambda x: EXECUTORS[x],
    )
    task_type = st.selectbox(
        "Тип задачи",
        options=["stock_task", "order_task"],
        format_func=lambda x: TYPE_LABELS[x],
    )
    dc1, dc2 = st.columns(2)
    dc1.date_input("Дата начала", value=datetime.date.today())
    dc2.date_input("Дедлайн", value=datetime.date.today() + datetime.timedelta(days=3))
    st.text_input("Комментарий", placeholder="Необязательно")

    st.divider()
    st.caption("Расчёт сырья выполняется автоматически при создании")

    if st.button("Создать", type="primary", use_container_width=True):
        st.success("Задача создана (демо)")
        st.rerun()


@st.dialog("Остановить задачу")
def _stop_task_dialog(task: dict):
    st.caption(f"Задача {_task_number(task)} — {PRODUCTS.get(task['product_id'], '?')}")
    reason = st.text_area("Причина остановки", placeholder="Обязательно укажите причину")
    if st.button("Остановить", type="primary", use_container_width=True):
        if not reason:
            st.error("Укажите причину остановки")
        else:
            st.success("Задача остановлена (демо)")
            st.rerun()


@st.dialog("Завершить задачу — отчёт")
def _complete_task_dialog(task: dict):
    st.caption(f"Задача {_task_number(task)} — {PRODUCTS.get(task['product_id'], '?')}")
    st.markdown("**Результат производства**")
    st.number_input("Фактическое количество (шт.)", min_value=0, value=task["quantity"])
    st.text_input("Комментарий", placeholder="Необязательно")

    st.divider()
    st.markdown("**Фактический расход сырья**")
    for rm in task.get("raw_materials", []):
        rm_name = RAW_MATERIALS.get(rm["rm_id"], f"#{rm['rm_id']}")
        rc1, rc2, rc3 = st.columns(3)
        rc1.text_input("Сырьё", value=rm_name, disabled=True, key=f"comp_rm_{rm['rm_id']}")
        rc2.number_input(
            "Фактически (кг)", min_value=0.0, value=float(rm["planned_qty"]),
            step=0.01, key=f"comp_actual_{rm['rm_id']}",
        )
        rc3.number_input(
            "Брак (кг)", min_value=0.0, value=0.0,
            step=0.01, key=f"comp_waste_{rm['rm_id']}",
        )

    if st.button("Завершить задачу", type="primary", use_container_width=True):
        st.success("Задача завершена (демо)")
        st.rerun()


@st.dialog("Переназначить исполнителя")
def _reassign_dialog(task: dict):
    st.caption(f"Задача {_task_number(task)} — {PRODUCTS.get(task['product_id'], '?')}")
    st.selectbox(
        "Новый исполнитель",
        options=list(EXECUTORS.keys()),
        format_func=lambda x: EXECUTORS[x],
    )
    if st.button("Сохранить", type="primary", use_container_width=True):
        st.success("Исполнитель изменён (демо)")
        st.rerun()


@st.dialog("Удалить задачу")
def _delete_task_dialog(task: dict):
    st.warning(
        f"Вы уверены, что хотите удалить задачу "
        f"**{_task_number(task)}** — {PRODUCTS.get(task['product_id'], '?')}?"
    )
    if st.button("Удалить", type="primary", use_container_width=True):
        st.success("Задача удалена (демо)")
        st.rerun()


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown("## Производственные задачи")

h1, h2 = st.columns([4, 1])
h2.button("+ Создать задачу", type="primary", use_container_width=True, key="btn_create", on_click=lambda: None)

if st.session_state.get("btn_create"):
    _create_task_dialog()


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

c1, c2 = st.columns([1, 1])
status_filter = c1.selectbox(
    "Статус", STATUS_OPTIONS,
    key="filter_status", label_visibility="collapsed",
)
executor_filter = c2.selectbox(
    "Исполнитель", ["Все"] + list(EXECUTORS.values()),
    key="filter_executor", label_visibility="collapsed",
)

filtered = _filter_tasks(TASKS, status_filter, executor_filter)
status_counts = {}
for t in TASKS:
    status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1


# ---------------------------------------------------------------------------
# Table + Drawer
# ---------------------------------------------------------------------------

df = _to_df(filtered)

if df.empty:
    st.info("Нет задач по выбранным фильтрам.")
elif _selected_rows("tbl_tasks"):
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_tasks")
    with col_dr:
        rows = sel.selection.rows
        if rows and rows[0] < len(filtered):
            task = filtered[rows[0]]

            # ---- Header ----
            st.markdown(f"### {_task_number(task)}")
            st.caption(
                f"{_status_label(task['status'])}  ·  "
                f"{TYPE_LABELS.get(task['task_type'], task['task_type'])}  ·  "
                f"Создана {task['created_at'].strftime('%d.%m.%Y')}"
            )

            # ---- Actions by status ----
            s = task["status"]

            if s == "Создана":
                ac1, ac2, ac3 = st.columns(3)
                if ac1.button("Начать", type="primary", key="dr_start"):
                    st.success("Задача запущена (демо)")
                if ac2.button("Переназначить", key="dr_reassign"):
                    _reassign_dialog(task)
                if ac3.button("🗑 Удалить", key="dr_delete"):
                    _delete_task_dialog(task)

            elif s == "В работе":
                ac1, ac2, ac3 = st.columns(3)
                if ac1.button("Остановить", key="dr_stop"):
                    _stop_task_dialog(task)
                if ac2.button("Завершить", type="primary", key="dr_complete"):
                    _complete_task_dialog(task)
                if ac3.button("Переназначить", key="dr_reassign"):
                    _reassign_dialog(task)

            elif s == "Остановлена":
                ac1, ac2, ac3 = st.columns(3)
                if ac1.button("Возобновить", type="primary", key="dr_resume"):
                    st.success("Задача возобновлена (демо)")
                if ac2.button("Переназначить", key="dr_reassign"):
                    _reassign_dialog(task)
                if ac3.button("🗑 Удалить", key="dr_delete"):
                    _delete_task_dialog(task)

            elif s == "Завершена":
                ac1, ac2 = st.columns(2)
                if ac1.button("Закрыть", type="primary", key="dr_close"):
                    st.success("Задача закрыта (демо)")
                if ac2.button("🗑 Удалить", key="dr_delete"):
                    _delete_task_dialog(task)

            elif s == "Закрыта":
                st.caption("Задача завершена и закрыта.")

            st.divider()

            # ---- Section: Основная информация ----
            st.markdown("**ЗАДАЧА**")
            _drawer_fields({
                "Продукт": PRODUCTS.get(task["product_id"], "?"),
                "Количество": f"{task['quantity']} шт",
                "Исполнитель": EXECUTORS.get(task["executor_id"], "?"),
                "Дата начала": task["start_date"].strftime("%d.%m.%Y"),
                "Дедлайн": task["deadline"].strftime("%d.%m.%Y"),
            })
            if task.get("comment"):
                _drawer_fields({"Комментарий": task["comment"]})
            if task.get("order_id"):
                _drawer_fields({"Заказ": f"#{task['order_id']}"})

            st.divider()

            # ---- Section: Время ----
            st.markdown("**ВРЕМЯ**")
            _drawer_fields({
                "Фактическое начало": task["actual_start_at"].strftime("%d.%m.%Y %H:%M") if task["actual_start_at"] else "—",
                "Фактическое окончание": task["actual_end_at"].strftime("%d.%m.%Y %H:%M") if task.get("actual_end_at") else "—",
            })

            # ---- Section: Остановки ----
            if task.get("stops"):
                st.divider()
                st.markdown("**ОСТАНОВКИ**")
                for stop in task["stops"]:
                    with st.container(border=True):
                        st.caption(f"Остановлена: {stop['stopped_at']}")
                        st.write(f"Причина: {stop['reason']}")
                        if stop.get("resumed_at"):
                            st.caption(f"Возобновлена: {stop['resumed_at']}")
                        else:
                            st.caption("Ожидает возобновления")

            st.divider()

            # ---- Section: Сырьё ----
            st.markdown("**СЫРЬЁ (резервы)**")
            for rm in task.get("raw_materials", []):
                rm_name = RAW_MATERIALS.get(rm["rm_id"], f"#{rm['rm_id']}")
                reserved = rm["reserved_qty"]
                planned = rm["planned_qty"]
                if reserved < planned:
                    st.write(f"**{rm_name}** — {reserved}/{planned} кг (недостаточно)")
                    st.progress(reserved / planned)
                else:
                    st.write(f"**{rm_name}** — {reserved} кг зарезервировано")
                    st.progress(1.0)

            # ---- Section: Результат (для завершённых / закрытых) ----
            if task.get("completion"):
                st.divider()
                st.markdown("**РЕЗУЛЬТАТ**")
                comp = task["completion"]
                _drawer_fields({
                    "Фактическое количество": f"{comp['actual_quantity']} шт",
                })
                if comp.get("comment"):
                    _drawer_fields({"Комментарий": comp["comment"]})

else:
    _table(df, key="tbl_tasks")


# ---------------------------------------------------------------------------
# Summary bar
# ---------------------------------------------------------------------------

total = len(TASKS)
shown = len(filtered)
if status_filter != "Все" or executor_filter != "Все":
    found_str = f"Найдено: **{shown}** из {total} задач"
else:
    found_str = f"Всего задач: **{total}**"

parts = [found_str]
for s_name in ["Создана", "В работе", "Остановлена", "Завершена"]:
    cnt = status_counts.get(s_name, 0)
    if cnt:
        parts.append(f"{STATUS_EMOJI.get(s_name, '')} {s_name}: **{cnt}**")

st.caption("   ·   ".join(parts))
