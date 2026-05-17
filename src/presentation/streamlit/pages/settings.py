import streamlit as st

from api_client import APIError, get_client

st.title("Настройки")

client = get_client()
roles = st.session_state.get("roles", [])
user_id = st.session_state.get("user_id")
is_director = "director" in roles


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Fetch current user info ───────────────────────────────────────────────────
try:
    me = client.get("/users/me")
    # Update cached full_name
    st.session_state["user_info"] = {"full_name": me.get("full_name", "")}
except APIError as e:
    _err(e)
    me = {}

st.write(f"**Пользователь:** {me.get('full_name', '')} ({me.get('username', '')})")
st.write(f"**Роли:** {', '.join(me.get('roles', []))}")
telegram = me.get("telegram_username")
st.write(f"**Telegram:** {telegram if telegram else 'не привязан'}")

st.divider()

# ── Section 1: Change password ────────────────────────────────────────────────
st.subheader("Сменить пароль")
with st.form("reset_password"):
    old_password = st.text_input("Текущий пароль", type="password")
    new_password = st.text_input("Новый пароль", type="password")
    new_password2 = st.text_input("Подтвердите новый пароль", type="password")
    if st.form_submit_button("Сохранить"):
        if new_password != new_password2:
            st.error("Пароли не совпадают.")
        elif len(new_password) < 6:
            st.error("Минимальная длина пароля — 6 символов.")
        else:
            try:
                client.post(
                    "/users/me/reset-password",
                    body={"old_password": old_password, "new_password": new_password},
                )
                st.success("Пароль изменён.")
            except APIError as e:
                _err(e)

st.divider()

# ── Section 2: Telegram ───────────────────────────────────────────────────────
st.subheader("Привязка Telegram")
with st.form("bind_telegram"):
    tg_username = st.text_input("Telegram username (без @)")
    if st.form_submit_button("Привязать"):
        if not tg_username:
            st.error("Введите username.")
        else:
            try:
                client.post(
                    "/users/me/bind-telegram",
                    body={"telegram_username": tg_username},
                )
                st.success("Telegram привязан.")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Section 3: User management (director only) ────────────────────────────────
if is_director:
    st.divider()
    st.subheader("Управление пользователями")

    include_inactive = st.checkbox("Показать неактивных", key="users_inactive")
    try:
        users = client.get("/users", include_inactive=include_inactive)
    except APIError as e:
        _err(e)
        users = []

    all_roles = ["director", "production", "warehouse", "delivery"]

    for u in users:
        status_icon = "🟢" if u["is_active"] else "🔴"
        with st.expander(f"{status_icon} {u['full_name']} ({u['username']}) — {', '.join(u['roles'])}"):
            tg = u.get("telegram_username")
            st.write(f"Telegram: {tg if tg else 'не привязан'}")

            # Roles
            current_roles = u.get("roles", [])
            new_roles = st.multiselect(
                "Роли",
                options=all_roles,
                default=current_roles,
                key=f"user_roles_{u['id']}",
            )
            if st.button("Сохранить роли", key=f"user_save_roles_{u['id']}"):
                try:
                    client.post(f"/users/{u['id']}/roles", body={"roles": new_roles})
                    st.success("Роли обновлены")
                    st.rerun()
                except APIError as e:
                    _err(e)

            # Activate/deactivate
            col1, col2 = st.columns(2)
            if u["is_active"]:
                if col1.button("Деактивировать", key=f"user_deact_{u['id']}"):
                    try:
                        client.post(f"/users/{u['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if col1.button("Активировать", key=f"user_act_{u['id']}"):
                    try:
                        client.post(f"/users/{u['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Создать пользователя")
    with st.form("create_user"):
        full_name = st.text_input("Полное имя")
        password = st.text_input("Пароль", type="password")
        user_roles = st.multiselect("Роли", options=all_roles)
        if st.form_submit_button("Создать"):
            if not full_name or not password:
                st.error("Заполните имя и пароль.")
            elif len(password) < 6:
                st.error("Минимальная длина пароля — 6 символов.")
            else:
                try:
                    result = client.post(
                        "/users",
                        body={"full_name": full_name, "password": password},
                    )
                    new_user_id = result["id"]
                    if user_roles:
                        client.post(
                            f"/users/{new_user_id}/roles",
                            body={"roles": user_roles},
                        )
                    st.success(f"Пользователь создан (id={new_user_id})")
                    st.rerun()
                except APIError as e:
                    _err(e)
