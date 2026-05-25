"""
SCR-016 — Пользователи
Демонстрация страницы. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_016_users.py
"""
import streamlit as st

st.set_page_config(
    page_title="SCR-016 — Пользователи (демо)",
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

import pandas as pd


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

CURRENT_USER = "tihomirov.e"

ROLE_LABELS = {
    "director": "Директор",
    "production": "Производство",
    "warehouse": "Склад",
    "delivery": "Доставка",
}

TG_STATUS_LABELS = {
    "linked": "Привязан",
    "pending": "Ожидает /start",
    "none": "Не указан",
}

TG_STATUS_ICONS = {
    "linked": "🟢",
    "pending": "🟡",
    "none": "⚪",
}

USERS = [
    {
        "id": 1,
        "full_name": "Евгений Тихомиров",
        "username": "tihomirov.e",
        "roles": ["director"],
        "tg_status": "linked",
        "tg_username": "@tihomirov_e",
        "is_active": True,
        "created_at": "18.03.2025",
        "created_by": "система",
    },
    {
        "id": 2,
        "full_name": "Иван Сидоров",
        "username": "sidorov.i",
        "roles": ["production"],
        "tg_status": "linked",
        "tg_username": "@sidorov_ivan",
        "is_active": True,
        "created_at": "18.04.2025",
        "created_by": "Тихомиров Е.С.",
    },
    {
        "id": 3,
        "full_name": "Дмитрий Иванов",
        "username": "ivanov.d",
        "roles": ["production", "delivery"],
        "tg_status": "linked",
        "tg_username": "@ivanov_dk",
        "tg_last_message": "14.05.2026 · 08:14",
        "is_active": True,
        "created_at": "18.04.2025",
        "created_by": "Тихомиров Е.С.",
    },
    {
        "id": 4,
        "full_name": "Анна Иванова",
        "username": "ivanova.a",
        "roles": ["warehouse"],
        "tg_status": "linked",
        "tg_username": "@ivanova_anna",
        "is_active": True,
        "created_at": "20.04.2025",
        "created_by": "Тихомиров Е.С.",
    },
    {
        "id": 5,
        "full_name": "Сергей Морозов",
        "username": "morozov.s",
        "roles": ["warehouse", "delivery"],
        "tg_status": "pending",
        "tg_username": None,
        "is_active": True,
        "created_at": "22.04.2025",
        "created_by": "Тихомиров Е.С.",
    },
    {
        "id": 6,
        "full_name": "Константин Петров",
        "username": "petrov.k",
        "roles": ["delivery"],
        "tg_status": "none",
        "tg_username": None,
        "is_active": True,
        "created_at": "25.04.2025",
        "created_by": "Тихомиров Е.С.",
    },
    {
        "id": 7,
        "full_name": "Алёна Петрова",
        "username": "petrova.a",
        "roles": ["production"],
        "tg_status": "none",
        "tg_username": None,
        "is_active": False,
        "created_at": "01.04.2025",
        "created_by": "Тихомиров Е.С.",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _roles_str(roles: list[str]) -> str:
    return ", ".join(ROLE_LABELS.get(r, r) for r in roles)


def _tg_label(status: str) -> str:
    icon = TG_STATUS_ICONS.get(status, "")
    label = TG_STATUS_LABELS.get(status, status)
    return f"{icon} {label}"


def _status_label(is_active: bool) -> str:
    return "Активен" if is_active else "Деактивирован"


def _to_df(users: list[dict]) -> pd.DataFrame:
    rows = []
    for u in users:
        name = u["full_name"]
        if u["username"] == CURRENT_USER:
            name += " (вы)"
        rows.append({
            "ФИО": name,
            "Username": u["username"],
            "Роли": _roles_str(u["roles"]),
            "Telegram": _tg_label(u["tg_status"]) if u["is_active"] else "—",
            "Статус": _status_label(u["is_active"]),
        })
    return pd.DataFrame(rows)


def _drawer_fields(fields: dict):
    for k, v in fields.items():
        col_k, col_v = st.columns([2, 3])
        col_k.caption(k)
        col_v.markdown(f"**{v}**")


def _selected_rows(key: str) -> list[int]:
    return st.session_state.get(key, {}).get("selection", {}).get("rows", [])


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Создать пользователя")
def _create_user_dialog():
    full_name = st.text_input("ФИО")
    username = st.text_input("Username (логин)")
    password = st.text_input("Пароль", type="password")

    role_options = list(ROLE_LABELS.keys())
    roles = st.multiselect(
        "Роли",
        options=role_options,
        format_func=lambda x: ROLE_LABELS[x],
    )

    if st.button("Создать", type="primary", use_container_width=True):
        if not full_name or not username or not password:
            st.error("Заполните все обязательные поля")
        elif not roles:
            st.error("Выберите хотя бы одну роль")
        else:
            st.success(f"Пользователь {username} создан (демо)")
            st.rerun()


@st.dialog("Редактировать пользователя")
def _edit_user_dialog(user: dict):
    full_name = st.text_input("ФИО", value=user["full_name"])

    role_options = list(ROLE_LABELS.keys())
    roles = st.multiselect(
        "Роли",
        options=role_options,
        default=user["roles"],
        format_func=lambda x: ROLE_LABELS[x],
    )

    if st.button("Сохранить", type="primary", use_container_width=True):
        if not full_name:
            st.error("ФИО не может быть пустым")
        elif not roles:
            st.error("Выберите хотя бы одну роль")
        else:
            st.success("Сохранено (демо)")
            st.rerun()


@st.dialog("Сбросить пароль")
def _reset_password_dialog(user: dict):
    st.caption(f"Пользователь: **{user['full_name']}** ({user['username']})")
    new_password = st.text_input("Новый пароль", type="password")
    if st.button("Сбросить", type="primary", use_container_width=True):
        if not new_password:
            st.error("Введите новый пароль")
        else:
            st.success("Пароль сброшен (демо)")
            st.rerun()


@st.dialog("Деактивировать пользователя")
def _deactivate_dialog(user: dict):
    st.warning(f"Вы уверены, что хотите деактивировать **{user['full_name']}**?")
    st.caption("Пользователь не сможет входить в систему, но данные сохранятся.")
    if st.button("Деактивировать", type="primary", use_container_width=True):
        st.success("Деактивирован (демо)")
        st.rerun()


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title("Пользователи")

h1, h2 = st.columns([4, 1])
if h2.button("+ Создать пользователя", type="primary", use_container_width=True):
    _create_user_dialog()


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

c1, c2 = st.columns(2)

status_options = ["all", "active", "inactive"]
status_labels = {"all": "Все", "active": "Активные", "inactive": "Деактивированные"}
status_filter = c1.selectbox(
    "Статус",
    options=status_options,
    format_func=lambda x: status_labels[x],
    label_visibility="collapsed",
)

role_options_filter = [None] + list(ROLE_LABELS.keys())
role_filter = c2.selectbox(
    "Роль",
    options=role_options_filter,
    format_func=lambda x: ROLE_LABELS.get(x, "Все роли") if x else "Все роли",
    label_visibility="collapsed",
)


# ---------------------------------------------------------------------------
# Filter users
# ---------------------------------------------------------------------------

filtered = USERS[:]
if status_filter == "active":
    filtered = [u for u in filtered if u["is_active"]]
elif status_filter == "inactive":
    filtered = [u for u in filtered if not u["is_active"]]

if role_filter:
    filtered = [u for u in filtered if role_filter in u["roles"]]


# ---------------------------------------------------------------------------
# Table + Drawer
# ---------------------------------------------------------------------------

df = _to_df(filtered)

sel_rows = _selected_rows("tbl_users")
sel_user = (
    filtered[sel_rows[0]]
    if sel_rows and sel_rows[0] < len(filtered)
    else None
)

if df.empty:
    st.info("Нет пользователей по выбранным фильтрам.")
elif sel_rows:
    col_tbl, col_dr = st.columns([3, 2])
    with col_tbl:
        sel = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="tbl_users",
        )
    with col_dr:
        rows = sel.selection.rows
        if rows and rows[0] < len(filtered):
            user = filtered[rows[0]]
            is_self = user["username"] == CURRENT_USER

            # Header
            st.markdown(f"### {user['full_name']}")
            status_text = "Активен" if user["is_active"] else "Деактивирован"
            st.caption(f"{user['username']} · Создан {user['created_at']} · {user['created_by']}")

            # Actions
            if not is_self:
                ac1, ac2, ac3 = st.columns(3)
                if ac1.button("Редактировать", key="dr_edit"):
                    _edit_user_dialog(user)
                if ac2.button("Сбросить пароль", key="dr_reset"):
                    _reset_password_dialog(user)
                if user["is_active"]:
                    if ac3.button("Деактивировать", key="dr_deact"):
                        _deactivate_dialog(user)
                else:
                    ac3.button("Активировать", key="dr_activate")
            else:
                st.info("Это ваша учётная запись")

            st.divider()

            # Section: Основное
            st.markdown("**ОСНОВНОЕ**")
            _drawer_fields({
                "ФИО": user["full_name"],
                "Username": user["username"],
                "Дата создания": user["created_at"],
            })

            st.markdown("**Роли:**")
            for role in user["roles"]:
                label = ROLE_LABELS.get(role, role)
                st.markdown(f"- {label}")

            st.divider()

            # Section: Telegram
            st.markdown("**TELEGRAM**")
            tg = user["tg_status"]
            if tg == "linked":
                _drawer_fields({
                    "Статус": "Привязан",
                    "TG-username": user.get("tg_username", "—"),
                })
                if user.get("tg_last_message"):
                    _drawer_fields({"Последнее сообщение боту": user["tg_last_message"]})
            elif tg == "pending":
                st.warning("Ожидает /start — пользователь ещё не написал боту")
            else:
                st.caption("Telegram не указан")
else:
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="tbl_users",
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

total = len(filtered)
active_count = len([u for u in filtered if u["is_active"]])
deact_count = total - active_count
tg_linked = len([u for u in filtered if u["tg_status"] == "linked" and u["is_active"]])
tg_pending = len([u for u in filtered if u["tg_status"] == "pending" and u["is_active"]])

parts = [f"Всего: **{total}**"]
if active_count:
    parts.append(f"Активных: **{active_count}**")
if deact_count:
    parts.append(f"Деактивированных: **{deact_count}**")
parts.append(f"🟢 TG привязан: **{tg_linked}**")
if tg_pending:
    parts.append(f"🟡 Ожидают /start: **{tg_pending}**")

st.caption("   ·   ".join(parts))
