import streamlit as st

from api_client import APIError, SessionExpiredError, get_client

st.set_page_config(page_title="АИС «Ярко»", layout="wide")


def _build_pages(roles: list[str]) -> list[st.Page]:
    role_set = set(roles)
    pages = []
    if "director" in role_set or "warehouse" in role_set:
        pages.append(st.Page("pages/warehouse.py", title="Склад"))
    if "director" in role_set or "production" in role_set:
        pages.append(st.Page("pages/tasks.py", title="Задачи"))
    if "director" in role_set or "delivery" in role_set:
        pages.append(st.Page("pages/deliveries.py", title="Доставки"))
    if "director" in role_set:
        pages.append(st.Page("pages/references.py", title="Справочники"))
        pages.append(st.Page("pages/orders.py", title="Заказы"))
    pages.append(st.Page("pages/settings.py", title="Настройки"))
    return pages


def main() -> None:
    tokens = st.session_state.get("tokens")

    if not tokens:
        pg = st.navigation([st.Page("pages/login.py", title="Вход")])
        pg.run()
        return

    try:
        roles = st.session_state.get("roles", [])
        pages = _build_pages(roles)

        with st.sidebar:
            user_info = st.session_state.get("user_info", {})
            if user_info.get("full_name"):
                st.caption(f"👤 {user_info['full_name']}")
            st.caption(", ".join(roles))
            st.divider()
            if st.button("Выйти", use_container_width=True):
                try:
                    client = get_client()
                    client.post(
                        "/auth/logout",
                        body={"refresh_token": tokens["refresh_token"]},
                    )
                except Exception:
                    pass
                st.session_state.clear()
                st.rerun()

        pg = st.navigation(pages)
        pg.run()

    except SessionExpiredError:
        st.session_state.clear()
        st.rerun()


main()
