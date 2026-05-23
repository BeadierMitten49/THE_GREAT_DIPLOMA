import datetime

import pandas as pd
import streamlit as st

from api_client import APIError, get_client

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles
is_production = "production" in roles

STATUS_OPTIONS = ["", "created", "in_progress", "stopped", "completed", "closed"]
STATUS_LABELS = {
    "": "Все",
    "created": "Создана",
    "in_progress": "В работе",
    "stopped": "Остановлена",
    "completed": "Завершена",
    "closed": "Закрыта",
}
STATUS_EMOJI = {
    "created": "⚪",
    "in_progress": "🔵",
    "stopped": "🟠",
    "completed": "🟢",
    "closed": "✅",
}
TYPE_LABELS = {
    "stock_task": "В запас",
    "order_task": "Под заказ",
}


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
    products = client.get("/references/products", include_inactive=False)
    product_map = {p["id"]: p["name"] for p in products}
    raw_materials_list = client.get("/references/raw-materials", include_inactive=False)
    rm_map = {rm["id"]: rm["name"] for rm in raw_materials_list}
    users = client.get("/users")
    prod_users = [u for u in users if "production" in u.get("roles", [])]
    prod_user_map = {u["id"]: u["full_name"] for u in prod_users}
except APIError as e:
    _err(e)
    product_map = {}
    rm_map = {}
    prod_user_map = {}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _task_number(task: dict) -> str:
    created = task.get("created_at", "")
    if created:
        year = int(created[:4]) % 100
    else:
        year = datetime.date.today().year % 100
    return f"T-{year}-{task['id']:04d}"


def _status_label(status: str) -> str:
    return f"{STATUS_EMOJI.get(status, '')} {STATUS_LABELS.get(status, status)}"


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


def _to_df(tasks: list[dict]) -> pd.DataFrame:
    rows = []
    for t in tasks:
        rows.append({
            "№": _task_number(t),
            "Продукт": product_map.get(t["product_id"], f"#{t['product_id']}"),
            "Кол-во": f"{t['quantity']} шт",
            "Исполнитель": prod_user_map.get(t["executor_id"], f"#{t['executor_id']}"),
            "Дедлайн": t["deadline"],
            "Тип": TYPE_LABELS.get(t["task_type"], t["task_type"]),
            "Статус": _status_label(t["status"]),
        })
    return pd.DataFrame(rows)


# ── Dialogs ───────────────────────────────────────────────────────────────────


@st.dialog("Создать задачу")
def _create_task_dialog():
    prod_ids = list(product_map.keys())
    if not prod_ids:
        st.warning("Нет продуктов в справочнике.")
        return
    prod_id = st.selectbox(
        "Продукт",
        options=prod_ids,
        format_func=lambda x: product_map.get(x, str(x)),
    )
    quantity = st.number_input("Количество (шт.)", min_value=1, value=100)

    exec_ids = list(prod_user_map.keys())
    if not exec_ids:
        st.warning("Нет исполнителей с ролью «Производство».")
        return
    executor_id = st.selectbox(
        "Исполнитель",
        options=exec_ids,
        format_func=lambda x: prod_user_map[x],
    )
    dc1, dc2 = st.columns(2)
    start_date = dc1.date_input("Дата начала", value=datetime.date.today())
    deadline = dc2.date_input("Дедлайн", value=datetime.date.today() + datetime.timedelta(days=3))
    comment = st.text_input("Комментарий", placeholder="Необязательно")

    if st.button("Создать", type="primary", use_container_width=True):
        try:
            result = client.post("/tasks", body={
                "product_id": prod_id,
                "quantity": quantity,
                "executor_id": executor_id,
                "task_type": "stock_task",
                "start_date": str(start_date),
                "deadline": str(deadline),
                "comment": comment if comment else None,
            })
            if result and result.get("insufficient_materials"):
                rm_names = [rm_map.get(rid, f"#{rid}") for rid in result["insufficient_materials"]]
                st.warning(f"Задача создана, но не хватает сырья: {', '.join(rm_names)}")
            else:
                st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Остановить задачу")
def _stop_task_dialog(task: dict):
    st.caption(f"Задача {_task_number(task)}")
    reason = st.text_area("Причина остановки", placeholder="Обязательно укажите причину")
    if st.button("Остановить", type="primary", use_container_width=True):
        if not reason:
            st.error("Укажите причину остановки")
        else:
            try:
                client.post(f"/tasks/{task['id']}/stop", body={"reason": reason})
                st.rerun()
            except APIError as e:
                _err(e)


@st.dialog("Завершить задачу — отчёт", width="large")
def _complete_task_dialog(task: dict, reservations: list[dict]):
    st.caption(f"Задача {_task_number(task)} — {task.get('product_name', '')}")
    st.markdown("**Результат производства**")
    actual_qty = st.number_input(
        "Фактическое количество (шт.)", min_value=0, value=task["quantity"],
    )
    complete_comment = st.text_input("Комментарий", placeholder="Необязательно")

    st.divider()
    st.markdown("**Фактический расход сырья**")

    # group reservations by raw material name
    rm_groups: dict[int, dict] = {}
    for r in reservations:
        rm_name = r["raw_material_name"]
        # try to extract rm_id from the name (we don't have it directly)
        # but we have it from rm_map
        rm_id_found = None
        for rid, rname in rm_map.items():
            if rname == rm_name:
                rm_id_found = rid
                break
        if rm_id_found is not None:
            if rm_id_found not in rm_groups:
                rm_groups[rm_id_found] = {"name": rm_name, "total": 0}
            rm_groups[rm_id_found]["total"] += float(r["quantity"])

    consumptions = []
    if rm_groups:
        for rm_id, info in rm_groups.items():
            rc1, rc2, rc3 = st.columns(3)
            rc1.text_input("Сырьё", value=info["name"], disabled=True, key=f"comp_rm_{rm_id}")
            actual_q = rc2.number_input(
                "Фактически (кг)", min_value=0.0, value=info["total"],
                step=0.01, key=f"comp_actual_{rm_id}",
            )
            waste_q = rc3.number_input(
                "Брак (кг)", min_value=0.0, value=0.0,
                step=0.01, key=f"comp_waste_{rm_id}",
            )
            consumptions.append({
                "raw_material_id": rm_id,
                "actual_qty": actual_q,
                "waste_qty": waste_q,
            })
    elif rm_map:
        n_cons = st.number_input("Строк расхода", min_value=0, max_value=20, value=0)
        rm_ids = list(rm_map.keys())
        for i in range(int(n_cons)):
            c1, c2, c3 = st.columns(3)
            rm_id = c1.selectbox(
                "Сырьё", options=rm_ids,
                format_func=lambda x: rm_map.get(x, str(x)),
                key=f"cons_rm_{i}",
            )
            actual_q = c2.number_input(
                "Фактически", min_value=0.0, step=0.01, key=f"cons_aq_{i}",
            )
            waste_q = c3.number_input(
                "Брак", min_value=0.0, step=0.01, key=f"cons_wq_{i}",
            )
            consumptions.append({
                "raw_material_id": rm_id,
                "actual_qty": actual_q,
                "waste_qty": waste_q,
            })

    if st.button("Завершить задачу", type="primary", use_container_width=True):
        try:
            client.post(f"/tasks/{task['id']}/complete", body={
                "actual_quantity": actual_qty,
                "comment": complete_comment if complete_comment else None,
                "consumptions": consumptions,
            })
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Переназначить исполнителя")
def _reassign_dialog(task: dict):
    st.caption(f"Задача {_task_number(task)}")
    exec_ids = list(prod_user_map.keys())
    new_exec = st.selectbox(
        "Новый исполнитель",
        options=exec_ids,
        format_func=lambda x: prod_user_map[x],
    )
    if st.button("Сохранить", type="primary", use_container_width=True):
        try:
            client.patch(f"/tasks/{task['id']}/assignee", body={"executor_id": new_exec})
            st.rerun()
        except APIError as e:
            _err(e)


@st.dialog("Удалить задачу")
def _delete_task_dialog(task: dict):
    st.warning(
        f"Вы уверены, что хотите удалить задачу "
        f"**{_task_number(task)}**?"
    )
    if st.button("Удалить", type="primary", use_container_width=True):
        try:
            client.delete(f"/tasks/{task['id']}")
            st.rerun()
        except APIError as e:
            _err(e)


# ── Page header ───────────────────────────────────────────────────────────────

st.title("Производственные задачи")

h1, h2 = st.columns([4, 1])
if is_director:
    if h2.button("+ Создать задачу", type="primary", use_container_width=True):
        _create_task_dialog()


# ── Filters ───────────────────────────────────────────────────────────────────

c1, c2 = st.columns([1, 1])
status_filter = c1.selectbox(
    "Статус", options=STATUS_OPTIONS,
    format_func=lambda x: STATUS_LABELS.get(x, x) if x else "Все",
    label_visibility="collapsed", key="filter_status",
)
executor_options = [None] + list(prod_user_map.keys())
executor_filter = c2.selectbox(
    "Исполнитель", options=executor_options,
    format_func=lambda x: prod_user_map.get(x, "Все исполнители") if x else "Все исполнители",
    label_visibility="collapsed", key="filter_executor",
)


# ── Load tasks ────────────────────────────────────────────────────────────────

try:
    tasks = client.get(
        "/tasks",
        status=status_filter if status_filter else None,
    )
    # client-side filter by executor (API supports it but let's filter locally for combined filters)
    if executor_filter is not None:
        tasks = [t for t in tasks if t["executor_id"] == executor_filter]
except APIError as e:
    _err(e)
    tasks = []


# ── Table + Drawer ────────────────────────────────────────────────────────────

df = _to_df(tasks)

sel_rows = _selected_rows("tbl_tasks")
sel_task = (
    tasks[sel_rows[0]]
    if sel_rows and sel_rows[0] < len(tasks)
    else None
)

if df.empty:
    if status_filter or executor_filter:
        st.info("Нет задач по выбранным фильтрам.")
    else:
        st.info("Задач пока нет.")
elif sel_rows:
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_tasks")
    with col_dr:
        rows = sel.selection.rows
        if rows and rows[0] < len(tasks):
            task_brief = tasks[rows[0]]

            # Load drawer data
            try:
                drawer = client.get(f"/tasks/{task_brief['id']}/drawer")
            except APIError as e:
                _err(e)
                drawer = None

            if drawer:
                t = drawer["task"]
                t["product_name"] = drawer["product_name"]
                stops = drawer["stops"]
                completion = drawer["completion"]
                reservations = drawer["reservations"]

                # ---- Header ----
                st.markdown(f"### {_task_number(t)}")
                st.caption(
                    f"{_status_label(t['status'])}  ·  "
                    f"{TYPE_LABELS.get(t['task_type'], t['task_type'])}  ·  "
                    f"Создана {t['created_at'][:10] if t.get('created_at') else '—'}"
                )

                # ---- Actions ----
                s = t["status"]

                if s == "created":
                    ac1, ac2, ac3 = st.columns(3)
                    if ac1.button("Начать", type="primary", key="dr_start"):
                        try:
                            client.post(f"/tasks/{t['id']}/start")
                            st.rerun()
                        except APIError as e:
                            _err(e)
                    if is_director:
                        if ac2.button("Переназначить", key="dr_reassign"):
                            _reassign_dialog(t)
                        if ac3.button("🗑 Удалить", key="dr_delete"):
                            _delete_task_dialog(t)

                elif s == "in_progress":
                    ac1, ac2, ac3 = st.columns(3)
                    if ac1.button("Остановить", key="dr_stop"):
                        _stop_task_dialog(t)
                    if ac2.button("Завершить", type="primary", key="dr_complete"):
                        _complete_task_dialog(t, reservations)
                    if is_director and ac3.button("Переназначить", key="dr_reassign"):
                        _reassign_dialog(t)

                elif s == "stopped":
                    ac1, ac2, ac3 = st.columns(3)
                    if ac1.button("Возобновить", type="primary", key="dr_resume"):
                        try:
                            client.post(f"/tasks/{t['id']}/resume")
                            st.rerun()
                        except APIError as e:
                            _err(e)
                    if is_director:
                        if ac2.button("Переназначить", key="dr_reassign"):
                            _reassign_dialog(t)
                        if ac3.button("🗑 Удалить", key="dr_delete"):
                            _delete_task_dialog(t)

                elif s == "completed" and is_director:
                    ac1, ac2 = st.columns(2)
                    if ac1.button("Закрыть", type="primary", key="dr_close"):
                        try:
                            client.post(f"/tasks/{t['id']}/close")
                            st.rerun()
                        except APIError as e:
                            _err(e)
                    if ac2.button("🗑 Удалить", key="dr_delete"):
                        _delete_task_dialog(t)

                elif s == "closed":
                    st.caption("Задача завершена и закрыта.")

                st.divider()

                # ---- Section: Основная информация ----
                st.markdown("**ЗАДАЧА**")
                _drawer_fields({
                    "Продукт": drawer["product_name"],
                    "Количество": f"{t['quantity']} шт",
                    "Исполнитель": drawer["executor_name"],
                    "Дата начала": t["start_date"],
                    "Дедлайн": t["deadline"],
                })
                if t.get("comment"):
                    _drawer_fields({"Комментарий": t["comment"]})
                if t.get("order_id"):
                    _drawer_fields({"Заказ": f"#{t['order_id']}"})

                st.divider()

                # ---- Section: Время ----
                st.markdown("**ВРЕМЯ**")
                _drawer_fields({
                    "Фактическое начало": t["actual_start_at"][:16].replace("T", " ") if t.get("actual_start_at") else "—",
                    "Фактическое окончание": t["actual_end_at"][:16].replace("T", " ") if t.get("actual_end_at") else "—",
                })

                # ---- Section: Остановки ----
                if stops:
                    st.divider()
                    st.markdown("**ОСТАНОВКИ**")
                    for stop in stops:
                        with st.container(border=True):
                            stopped_at = stop["stopped_at"][:16].replace("T", " ") if stop.get("stopped_at") else "?"
                            st.caption(f"Остановлена: {stopped_at}")
                            st.write(f"Причина: {stop['reason']}")
                            if stop.get("resumed_at"):
                                resumed_at = stop["resumed_at"][:16].replace("T", " ")
                                st.caption(f"Возобновлена: {resumed_at}")
                            else:
                                st.caption("Ожидает возобновления")

                # ---- Section: Сырьё (резервы) ----
                if reservations:
                    st.divider()
                    st.markdown("**СЫРЬЁ (резервы)**")
                    for r in reservations:
                        st.write(
                            f"**{r['raw_material_name']}** — "
                            f"{r['quantity']} кг · {r['batch_label']}"
                        )

                # ---- Section: Результат ----
                if completion:
                    st.divider()
                    st.markdown("**РЕЗУЛЬТАТ**")
                    _drawer_fields({
                        "Фактическое количество": f"{completion['actual_quantity']} шт",
                    })
                    if completion.get("comment"):
                        _drawer_fields({"Комментарий": completion["comment"]})

                    if completion.get("consumptions"):
                        st.markdown("**Расход сырья:**")
                        for c in completion["consumptions"]:
                            waste_str = f" · брак {c['waste_qty']} кг" if c.get("waste_qty") else ""
                            st.caption(
                                f"{c['raw_material_name']} — "
                                f"план {c['planned_qty']} кг, факт {c['actual_qty']} кг{waste_str}"
                            )
else:
    _table(df, key="tbl_tasks")


# ── Summary bar ───────────────────────────────────────────────────────────────

total = len(tasks)
status_counts: dict[str, int] = {}
for t in tasks:
    status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1

if status_filter or executor_filter:
    found_str = f"Найдено: **{total}** задач"
else:
    found_str = f"Всего задач: **{total}**"

parts = [found_str]
for s in ["created", "in_progress", "stopped", "completed"]:
    cnt = status_counts.get(s, 0)
    if cnt:
        parts.append(f"{STATUS_EMOJI.get(s, '')} {STATUS_LABELS.get(s, s)}: **{cnt}**")

st.caption("   ·   ".join(parts))
