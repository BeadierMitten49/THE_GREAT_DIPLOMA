import streamlit as st

from api_client import APIError, get_client

st.title("Производственные задачи")

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load reference data ───────────────────────────────────────────────────────
try:
    products = client.get("/references/products", include_inactive=False)
    product_map = {p["id"]: p["name"] for p in products}
    raw_materials_list = client.get("/references/raw-materials", include_inactive=False)
    rm_map = {rm["id"]: rm["name"] for rm in raw_materials_list}
    if is_director:
        users = client.get("/users")
        prod_users = [u for u in users if "production" in u.get("roles", [])]
        prod_user_map = {u["id"]: u["full_name"] for u in prod_users}
    else:
        prod_user_map = {}
except APIError as e:
    _err(e)
    product_map = {}
    rm_map = {}
    prod_user_map = {}

# ── Filters ───────────────────────────────────────────────────────────────────
status_filter = st.selectbox(
    "Статус",
    options=["", "pending", "in_progress", "stopped", "completed", "closed", "cancelled"],
    format_func=lambda x: x if x else "Все",
)

# ── Task list ─────────────────────────────────────────────────────────────────
try:
    tasks = client.get("/tasks", status=status_filter if status_filter else None)
except APIError as e:
    _err(e)
    tasks = []

for t in tasks:
    prod_name = product_map.get(t["product_id"], f"id={t['product_id']}")
    label = f"#{t['id']} — {prod_name} — {t['quantity']} шт. — {t['status']} — до {t['deadline']}"
    with st.expander(label):
        executor_name = prod_user_map.get(t["executor_id"], f"id={t['executor_id']}")
        st.write(f"Исполнитель: {executor_name}")
        st.write(f"Тип: {t['task_type']} | Начало: {t['start_date']} | Дедлайн: {t['deadline']}")
        if t.get("comment"):
            st.write(f"Комментарий: {t['comment']}")
        if t.get("order_id"):
            st.write(f"Заказ: #{t['order_id']}")

        s = t["status"]

        if s == "pending":
            if st.button("Начать", key=f"task_start_{t['id']}"):
                try:
                    client.post(f"/tasks/{t['id']}/start")
                    st.rerun()
                except APIError as e:
                    _err(e)

        elif s == "in_progress":
            col1, col2 = st.columns(2)
            if col1.button("Остановить", key=f"task_stop_{t['id']}"):
                st.session_state[f"task_stop_open_{t['id']}"] = True
            if st.session_state.get(f"task_stop_open_{t['id']}"):
                with st.form(f"stop_form_{t['id']}"):
                    reason = st.text_input("Причина остановки")
                    if st.form_submit_button("Подтвердить"):
                        try:
                            client.post(f"/tasks/{t['id']}/stop", body={"reason": reason})
                            st.session_state.pop(f"task_stop_open_{t['id']}", None)
                            st.rerun()
                        except APIError as e:
                            _err(e)

            if col2.button("Завершить", key=f"task_complete_{t['id']}"):
                st.session_state[f"task_complete_open_{t['id']}"] = True
            if st.session_state.get(f"task_complete_open_{t['id']}"):
                with st.form(f"complete_form_{t['id']}"):
                    actual_qty = st.number_input("Фактическое количество", min_value=0, value=t["quantity"])
                    complete_comment = st.text_input("Комментарий (необязательно)")
                    st.write("**Расход сырья:**")
                    consumptions = []
                    if rm_map:
                        n_cons = st.number_input("Строк расхода", min_value=0, max_value=20, value=0)
                        rm_ids = list(rm_map.keys())
                        for i in range(int(n_cons)):
                            c1, c2, c3 = st.columns(3)
                            rm_id = c1.selectbox(
                                "Сырьё", options=rm_ids,
                                format_func=lambda x: rm_map.get(x, x),
                                key=f"cons_rm_{t['id']}_{i}",
                            )
                            actual_q = c2.number_input(
                                "Фактически", min_value=0.0, step=0.01,
                                key=f"cons_aq_{t['id']}_{i}",
                            )
                            waste_q = c3.number_input(
                                "Брак", min_value=0.0, step=0.01,
                                key=f"cons_wq_{t['id']}_{i}",
                            )
                            consumptions.append({
                                "raw_material_id": rm_id,
                                "actual_qty": actual_q,
                                "waste_qty": waste_q,
                            })
                    if st.form_submit_button("Завершить задачу"):
                        try:
                            client.post(
                                f"/tasks/{t['id']}/complete",
                                body={
                                    "actual_quantity": actual_qty,
                                    "comment": complete_comment if complete_comment else None,
                                    "consumptions": consumptions,
                                },
                            )
                            st.session_state.pop(f"task_complete_open_{t['id']}", None)
                            st.rerun()
                        except APIError as e:
                            _err(e)

        elif s == "stopped":
            if st.button("Возобновить", key=f"task_resume_{t['id']}"):
                try:
                    client.post(f"/tasks/{t['id']}/resume")
                    st.rerun()
                except APIError as e:
                    _err(e)

        elif s == "completed" and is_director:
            if st.button("Закрыть", key=f"task_close_{t['id']}"):
                try:
                    client.post(f"/tasks/{t['id']}/close")
                    st.rerun()
                except APIError as e:
                    _err(e)

        if is_director:
            st.divider()
            col_r, col_d = st.columns(2)
            if col_r.button("Переназначить", key=f"task_reassign_{t['id']}"):
                st.session_state[f"task_reassign_open_{t['id']}"] = True
            if st.session_state.get(f"task_reassign_open_{t['id']}") and prod_user_map:
                new_exec = st.selectbox(
                    "Новый исполнитель",
                    options=list(prod_user_map.keys()),
                    format_func=lambda x: prod_user_map[x],
                    key=f"task_new_exec_{t['id']}",
                )
                if st.button("Сохранить", key=f"task_reassign_save_{t['id']}"):
                    try:
                        client.patch(f"/tasks/{t['id']}/assignee", body={"executor_id": new_exec})
                        st.session_state.pop(f"task_reassign_open_{t['id']}", None)
                        st.rerun()
                    except APIError as e:
                        _err(e)

            if col_d.button("Удалить", key=f"task_del_{t['id']}"):
                try:
                    client.delete(f"/tasks/{t['id']}")
                    st.rerun()
                except APIError as e:
                    _err(e)

# ── Create task (director only) ───────────────────────────────────────────────
if is_director:
    st.divider()
    st.subheader("Создать задачу")
    if not product_map or not prod_user_map:
        st.info("Для создания задачи необходимы товары и сотрудники производства.")
    else:
        with st.form("create_task"):
            prod_id = st.selectbox(
                "Товар",
                options=list(product_map.keys()),
                format_func=lambda x: product_map[x],
            )
            quantity = st.number_input("Количество (шт.)", min_value=1, value=1)
            executor_id = st.selectbox(
                "Исполнитель",
                options=list(prod_user_map.keys()),
                format_func=lambda x: prod_user_map[x],
            )
            task_type = st.selectbox("Тип задачи", options=["production", "repackaging"])
            start_date = st.date_input("Дата начала")
            deadline = st.date_input("Дедлайн")
            task_comment = st.text_input("Комментарий")
            if st.form_submit_button("Создать"):
                try:
                    result = client.post(
                        "/tasks",
                        body={
                            "product_id": prod_id,
                            "quantity": quantity,
                            "executor_id": executor_id,
                            "task_type": task_type,
                            "start_date": str(start_date),
                            "deadline": str(deadline),
                            "comment": task_comment if task_comment else None,
                        },
                    )
                    if result and result.get("insufficient_materials"):
                        st.warning(
                            f"Задача создана, но не хватает сырья: "
                            f"{result['insufficient_materials']}"
                        )
                    else:
                        st.success("Задача создана")
                    st.rerun()
                except APIError as e:
                    _err(e)
