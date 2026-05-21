"""
SCR-001 — Вход в систему
Демонстрация всех 7 состояний. Без подключения к API.

Запуск:
    streamlit run page_examples/scr_001_login.py
"""
import streamlit as st

st.set_page_config(
    page_title="SCR-001 — Вход (демо)",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("### SCR-001 — Вход в систему")
st.caption("Демонстрация 7 состояний · без подключения к API")
st.divider()


# ---------------------------------------------------------------------------
# CSS — base styles, injected once at page level
# ---------------------------------------------------------------------------

st.markdown("""
<style>
.stApp { background: #F5F6F8 !important; }
#MainMenu, header, footer { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
div.block-container {
    max-width: 480px !important;
    padding: 60px 0 40px !important;
    margin: 0 auto !important;
}
div[data-testid="stForm"] {
    background: #FFFFFF !important;
    border: 0.5px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 40px !important;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06) !important;
}
div[data-testid="stTextInputRootElement"] label p {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #334155 !important;
    margin-bottom: 4px !important;
}
div[data-testid="stTextInputRootElement"] input {
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    height: 40px !important;
    font-size: 14px !important;
    color: #0F172A !important;
    box-shadow: none !important;
}
div[data-testid="stFormSubmitButton"] > button {
    width: 100% !important;
    height: 44px !important;
    background-color: #1E293B !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Shared fragments
# ---------------------------------------------------------------------------

# Логотип — цветной квадрат средствами Streamlit невозможен, минимальный HTML
_BRAND = """
<div style="display:flex;align-items:center;gap:12px;margin-bottom:24px">
  <div style="width:48px;height:48px;background:#0F172A;border-radius:8px;flex-shrink:0"></div>
  <span style="font-size:18px;font-weight:500;color:#0F172A;letter-spacing:0.02em">ЯРКО</span>
</div>
"""


def _show_locked_card() -> None:
    st.markdown(_BRAND, unsafe_allow_html=True)
    st.markdown("## Вход в систему")
    st.error(
        "🔒 **Вход временно заблокирован**\n\n"
        "Превышено количество попыток входа. "
        "Попробуйте снова через 30 минут или обратитесь к директору.",
        icon=None,
    )


def _show_form(
    *,
    form_key: str,
    username: str = "",
    password_filled: bool = False,
    invalid: bool = False,
    deactivated: bool = False,
    network: bool = False,
    empty_password: bool = False,
    disabled: bool = False,
) -> None:
    with st.form(form_key):
        st.markdown(_BRAND, unsafe_allow_html=True)
        st.markdown("## Вход в систему")

        st.text_input(
            "Имя пользователя",
            value=username,
            placeholder="Введите логин",
            disabled=disabled,
        )
        st.text_input(
            "Пароль",
            value="demo_password" if password_filled else "",
            type="password",
            placeholder="Введите пароль",
            disabled=disabled,
        )

        if empty_password:
            st.markdown(
                '<p style="font-size:12px;color:#B91C1C;margin:-8px 0 8px">Заполните это поле</p>',
                unsafe_allow_html=True,
            )

        if invalid:
            st.warning("⚠ Неверное имя пользователя или пароль")
        elif deactivated:
            st.warning("🚫 Учётная запись деактивирована. Обратитесь к директору.")
        elif network:
            st.warning("⚠ Нет связи с сервером. Проверьте подключение.")

        if disabled:
            st.form_submit_button("Вход…", disabled=True, use_container_width=True)
        else:
            st.form_submit_button("Войти", use_container_width=True)

    st.caption("АИС «Ярко» · ООО ТД «Ярко» · 2026")


# ---------------------------------------------------------------------------
# 7 состояний
# ---------------------------------------------------------------------------

STATES = [
    {
        "tab": "1 · Default",
        "desc": "Поля пустые — кнопка «Войти» активна (ввод не проверяется до сабмита).",
        "form": {"form_key": "form_1"},
    },
    {
        "tab": "2 · Filled-active",
        "desc": "Оба поля заполнены — кнопка «Войти» активна (тёмная).",
        "form": {"form_key": "form_2", "username": "ivanov.i", "password_filled": True},
    },
    {
        "tab": "3 · Submitting",
        "desc": "Запрос отправлен — поля заблокированы, кнопка показывает «Вход…».",
        "form": {"form_key": "form_3", "username": "ivanov.i", "password_filled": True, "disabled": True},
    },
    {
        "tab": "4 · Error-invalid",
        "desc": "API → 401 · Неверный логин или пароль — сообщение об ошибке.",
        "form": {"form_key": "form_4", "username": "ivanov.i", "password_filled": True, "invalid": True},
    },
    {
        "tab": "5 · Error-deactivated",
        "desc": "API → 403 · Учётная запись деактивирована директором.",
        "form": {"form_key": "form_5", "username": "petrov.p", "password_filled": True, "deactivated": True},
    },
    {
        "tab": "6 · Validation-empty",
        "desc": "Submit при пустом пароле — подпись под полем пароля.",
        "form": {"form_key": "form_6", "username": "ivanov.i", "empty_password": True},
    },
    {
        "tab": "7 · Locked",
        "desc": "API → 429 · Превышено число попыток — блок-предупреждение, форма скрыта.",
        "form": None,  # locked — нет формы
    },
]

tabs = st.tabs([s["tab"] for s in STATES])
for tab, state in zip(tabs, STATES):
    with tab:
        st.caption(state["desc"])
        if state["form"] is None:
            _show_locked_card()
        else:
            _show_form(**state["form"])
