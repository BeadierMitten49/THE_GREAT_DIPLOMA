import httpx
import streamlit as st

from api_client import API_BASE_URL, decode_token_payload

st.title("АИС «Ярко»")
st.subheader("Вход в систему")

with st.form("login"):
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")
    submitted = st.form_submit_button("Войти", use_container_width=True)

if submitted:
    if not username or not password:
        st.error("Введите логин и пароль.")
    else:
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
                st.session_state["user_info"] = {"full_name": username}
                st.rerun()
            elif resp.status_code == 429:
                st.error("Аккаунт заблокирован. Попробуйте через 30 минут.")
            else:
                st.error("Неверный логин или пароль.")
        except httpx.RequestError:
            st.error("Нет связи с сервером.")
