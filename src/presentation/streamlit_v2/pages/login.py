"""
Страница входа в систему АИС «Ярко».

Запускается через st.Page("pages/login.py") в app.py.
st.set_page_config и layout="wide" уже применены в app.py.
"""
import httpx
import streamlit as st

from api_client import API_BASE_URL, decode_token_payload


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
.stApp { background: #F5F6F8 !important; }
#MainMenu, header, footer { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
div.block-container {
    max-width: 480px !important;
    padding: 80px 0 40px !important;
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
    transition: background 0.15s ease !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #334155 !important;
}
div[data-testid="stFormSubmitButton"] > button:disabled {
    background-color: #E2E8F0 !important;
    color: #94A3B8 !important;
    cursor: not-allowed !important;
}
</style>
""", unsafe_allow_html=True)

# Логотип — цветной квадрат средствами Streamlit невозможен, минимальный HTML
_BRAND = """
<div style="display:flex;align-items:center;gap:12px;margin-bottom:24px">
  <div style="width:48px;height:48px;background:#0F172A;border-radius:8px;flex-shrink:0"></div>
  <span style="font-size:18px;font-weight:500;color:#0F172A;letter-spacing:0.02em">ЯРКО</span>
</div>
"""


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def _do_login(username: str, password: str) -> None:
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{API_BASE_URL}/auth/login",
                json={"username": username, "password": password},
            )

        if resp.status_code == 200:
            data = resp.json()
            payload = decode_token_payload(data["access_token"])
            st.session_state["tokens"] = {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
            }
            st.session_state["roles"] = payload.get("roles", [])
            st.session_state["user_id"] = int(payload["sub"])
            try:
                with httpx.Client(timeout=10.0) as c:
                    me = c.get(
                        f"{API_BASE_URL}/users/me",
                        headers={"Authorization": f"Bearer {data['access_token']}"},
                    )
                full_name = (
                    me.json().get("full_name", username)
                    if me.status_code == 200
                    else username
                )
            except Exception:
                full_name = username
            st.session_state["user_info"] = {"full_name": full_name}
            for k in ("login_error", "login_empty_password"):
                st.session_state.pop(k, None)

        elif resp.status_code == 401:
            st.session_state["login_error"] = "invalid"
        elif resp.status_code == 403:
            st.session_state["login_error"] = "deactivated"
        elif resp.status_code == 429:
            st.session_state["login_error"] = "locked"
        else:
            st.session_state["login_error"] = "invalid"

    except httpx.RequestError:
        st.session_state["login_error"] = "network"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

error: str | None = st.session_state.get("login_error")
empty_pw: bool = st.session_state.get("login_empty_password", False)

# Состояние 7: Locked — форма не нужна
if error == "locked":
    st.markdown(_BRAND, unsafe_allow_html=True)
    st.markdown("## Вход в систему")
    st.error(
        "🔒 **Вход временно заблокирован**\n\n"
        "Превышено количество попыток входа. "
        "Попробуйте снова через 30 минут или обратитесь к директору.",
        icon=None,
    )

# Состояния 1–6: Форма
else:
    with st.form("login_form"):
        st.markdown(_BRAND, unsafe_allow_html=True)
        st.markdown("## Вход в систему")

        username = st.text_input("Имя пользователя", placeholder="Введите логин")
        password = st.text_input("Пароль", type="password", placeholder="Введите пароль")

        # Состояние 6: пустой пароль — подпись под полем
        if empty_pw:
            st.markdown(
                '<p style="font-size:12px;color:#B91C1C;margin:-8px 0 8px">'
                "Заполните это поле</p>",
                unsafe_allow_html=True,
            )

        # Состояния 4, 5, network — предупреждение над кнопкой
        if error == "invalid":
            st.warning("⚠ Неверное имя пользователя или пароль")
        elif error == "deactivated":
            st.warning("🚫 Учётная запись деактивирована. Обратитесь к директору.")
        elif error == "network":
            st.warning("⚠ Нет связи с сервером. Проверьте подключение.")

        submitted = st.form_submit_button("Войти", use_container_width=True)

    st.caption("АИС «Ярко» · ООО ТД «Ярко» · 2026")

    if submitted:
        for k in ("login_error", "login_empty_password"):
            st.session_state.pop(k, None)

        if not password:
            st.session_state["login_empty_password"] = True
            st.rerun()
        elif not username:
            st.session_state["login_error"] = "invalid"
            st.rerun()
        else:
            _do_login(username, password)
            st.rerun()
