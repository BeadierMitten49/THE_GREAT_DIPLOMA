import pandas as pd
import streamlit as st

from api_client import APIError, get_client

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles
current_user_id = st.session_state.get("user_id")

ROLE_LABELS = {
    "director": "Директор",
    "production": "Производство",
    "warehouse": "Склад",
    "delivery": "Доставка",
}
ALL_ROLES = list(ROLE_LABELS.keys())


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


# ── Helpers ───────────────────────────────────────────────────────────────────


def _roles_str(user_roles: list[str]) -> str:
    return ", ".join(ROLE_LABELS.get(r, r) for r in user_roles)


def _tg_label(user: dict) -> str:
    tg = user.get("telegram_username")
    if tg:
        return f"🟢 {tg}"
    return "⚪ Не привязан"


def _to_df(users: list[dict]) -> pd.DataFrame:
    rows = []
    for u in users:
        name = u["full_name"]
        if u["id"] == current_user_id:
            name += " (вы)"
        rows.append({
            "ФИО": name,
            "Username": u["username"],
            "Роли": _roles_str(u.get("roles", [])),
            "Telegram": _tg_label(u),
            "Статус": "Активен" if u["is_active"] else "Деактивирован",
        })
    return pd.DataFrame(rows)


def _drawer_fields(fields: dict):
    for k, v in fields.items():
        col_k, col_v = st.columns([2, 3])
        col_k.caption(k)
        col_v.markdown(f"**{v}**")


def _selected_rows(key: str) -> list[int]:
    return st.session_state.get(key, {}).get("selection", {}).get("rows", [])


def _table(df: pd.DataFrame, key: str):
    return st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )


# ── Dialogs ───────────────────────────────────────────────────────────────────


@st.dialog("Создать пользователя")
def _create_user_dialog():
    full_name = st.text_input("ФИО")
    password = st.text_input("Пароль", type="password")
    user_roles = st.multiselect(
        "Роли",
        options=ALL_ROLES,
        format_func=lambda x: ROLE_LABELS[x],
    )

    if st.button("Создать", type="primary", use_container_width=True):
        if not full_name or not password:
            st.error("Заполните ФИО и пароль")
        elif len(password) < 6:
            st.error("Минимальная длина пароля — 6 символов")
        else:
            try:
                result = client.post("/users", body={
                    "full_name": full_name,
                    "password": password,
                })
                new_id = result["id"]
                if user_roles:
                    client.post(f"/users/{new_id}/roles", body={"roles": user_roles})
                st.success(f"Пользователь создан (username будет сгенерирован)")
                st.rerun()
            except APIError as e:
                _err(e)


@st.dialog("Редактировать пользователя")
def _edit_user_dialog(user: dict):
    full_name = st.text_input("ФИО", value=user["full_name"])
    user_roles = st.multiselect(
        "Роли",
        options=ALL_ROLES,
        default=user.get("roles", []),
        format_func=lambda x: ROLE_LABELS[x],
    )

    if st.button("Сохранить", type="primary", use_container_width=True):
        if not full_name:
            st.error("ФИО не может быть пустым")
        elif not user_roles:
            st.error("Выберите хотя бы одну роль")
        else:
            try:
                if full_name != user["full_name"]:
                    client.patch(f"/users/{user['id']}", body={"full_name": full_name})
                if set(user_roles) != set(user.get("roles", [])):
                    client.post(f"/users/{user['id']}/roles", body={"roles": user_roles})
                st.rerun()
            except APIError as e:
                _err(e)


@st.dialog("Деактивировать пользователя")
def _deactivate_dialog(user: dict):
    st.warning(f"Вы уверены, что хотите деактивировать **{user['full_name']}**?")
    st.caption("Пользователь не сможет входить в систему, но данные сохранятся.")
    if st.button("Деактивировать", type="primary", use_container_width=True):
        try:
            client.post(f"/users/{user['id']}/deactivate")
            st.rerun()
        except APIError as e:
            _err(e)


# ── Page header ───────────────────────────────────────────────────────────────

st.title("Пользователи")

h1, h2 = st.columns([4, 1])
if is_director:
    if h2.button("+ Создать пользователя", type="primary", use_container_width=True):
        _create_user_dialog()


# ── Filters ───────────────────────────────────────────────────────────────────

c1, c2 = st.columns(2)

status_options = ["all", "active", "inactive"]
status_labels_map = {"all": "Все", "active": "Активные", "inactive": "Деактивированные"}
status_filter = c1.selectbox(
    "Статус",
    options=status_options,
    format_func=lambda x: status_labels_map[x],
    label_visibility="collapsed",
)

role_options = [None] + ALL_ROLES
role_filter = c2.selectbox(
    "Роль",
    options=role_options,
    format_func=lambda x: ROLE_LABELS.get(x, "Все роли") if x else "Все роли",
    label_visibility="collapsed",
)


# ── Load users ────────────────────────────────────────────────────────────────

try:
    include_inactive = status_filter != "active"
    all_users = client.get("/users", include_inactive=include_inactive)
except APIError as e:
    _err(e)
    all_users = []

filtered = all_users
if status_filter == "active":
    filtered = [u for u in filtered if u["is_active"]]
elif status_filter == "inactive":
    filtered = [u for u in filtered if not u["is_active"]]

if role_filter:
    filtered = [u for u in filtered if role_filter in u.get("roles", [])]


# ── Table + Drawer ────────────────────────────────────────────────────────────

df = _to_df(filtered)

sel_rows = _selected_rows("tbl_users")
sel_user = (
    filtered[sel_rows[0]]
    if sel_rows and sel_rows[0] < len(filtered)
    else None
)

if df.empty:
    if status_filter != "all" or role_filter:
        st.info("Нет пользователей по выбранным фильтрам.")
    else:
        st.info("Пользователей пока нет.")
elif sel_rows:
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = _table(df, key="tbl_users")
    with col_dr:
        rows = sel.selection.rows
        if rows and rows[0] < len(filtered):
            user = filtered[rows[0]]
            is_self = user["id"] == current_user_id

            # Header
            st.markdown(f"### {user['full_name']}")
            st.caption(f"{user['username']} · {'Активен' if user['is_active'] else 'Деактивирован'}")

            # Actions
            if is_director and not is_self:
                ac1, ac2 = st.columns(2)
                if ac1.button("Редактировать", key="dr_edit"):
                    _edit_user_dialog(user)
                if user["is_active"]:
                    if ac2.button("Деактивировать", key="dr_deact"):
                        _deactivate_dialog(user)
                else:
                    if ac2.button("Активировать", key="dr_activate"):
                        try:
                            client.post(f"/users/{user['id']}/activate")
                            st.rerun()
                        except APIError as e:
                            _err(e)
            elif is_self:
                st.info("Это ваша учётная запись")

            st.divider()

            # Section: Основное
            st.markdown("**ОСНОВНОЕ**")
            _drawer_fields({
                "ФИО": user["full_name"],
                "Username": user["username"],
            })

            st.markdown("**Роли:**")
            for r in user.get("roles", []):
                st.markdown(f"- {ROLE_LABELS.get(r, r)}")

            st.divider()

            # Section: Telegram (заглушка)
            st.markdown("**TELEGRAM**")
            tg = user.get("telegram_username")
            if tg:
                _drawer_fields({"TG-username": tg})
            else:
                st.caption("Не привязан")
else:
    _table(df, key="tbl_users")


# ── Summary ───────────────────────────────────────────────────────────────────

total = len(filtered)
active_count = len([u for u in filtered if u["is_active"]])
deact_count = total - active_count

parts = [f"Всего: **{total}**"]
if active_count:
    parts.append(f"Активных: **{active_count}**")
if deact_count:
    parts.append(f"Деактивированных: **{deact_count}**")

st.caption("   ·   ".join(parts))
