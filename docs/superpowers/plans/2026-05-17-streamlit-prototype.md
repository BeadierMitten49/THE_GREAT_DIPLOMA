# Streamlit Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Streamlit prototype UI for АИС «Ярко» covering login, references, orders, tasks, warehouse, deliveries, and settings pages — communicating with the existing FastAPI backend via HTTP.

**Architecture:** `app.py` is the entry point with `st.navigation()` routing; role-based page list is built from JWT payload stored in `st.session_state`. `api_client.py` wraps all httpx calls with token management and auto-refresh. Each page is an isolated script in `pages/`.

**Tech Stack:** Streamlit, httpx (sync), python-jose (JWT decode), FastAPI backend at `http://localhost:8000/api/v1`.

---

## File Map

**New files:**
- `src/presentation/streamlit/app.py` — entry point, auth gate, navigation
- `src/presentation/streamlit/api_client.py` — httpx wrapper, token refresh, errors
- `src/presentation/streamlit/pages/login.py`
- `src/presentation/streamlit/pages/references.py`
- `src/presentation/streamlit/pages/orders.py`
- `src/presentation/streamlit/pages/tasks.py`
- `src/presentation/streamlit/pages/warehouse.py`
- `src/presentation/streamlit/pages/deliveries.py`
- `src/presentation/streamlit/pages/settings.py`

**New FastAPI file (required for non-director settings):**
- `src/presentation/api/v1/auth/me.py` — `/users/me` endpoints (all authenticated users)

**Modified:**
- `src/presentation/api/v1/__init__.py` — include me_router

---

## Task 0: Create feature branch

- [ ] **Step 1: Create branch**

```bash
git checkout develop
git pull
git checkout -b feature/streamlit
```

---

## Task 1: Add `/users/me` router to FastAPI

The `/users` router is `director_only`. Non-director users need `GET /users/me`,
`POST /users/me/reset-password`, `POST /users/me/bind-telegram` for the settings page.

**Files:**
- Create: `src/presentation/api/v1/auth/me.py`
- Modify: `src/presentation/api/v1/__init__.py`

- [ ] **Step 1: Create `src/presentation/api/v1/auth/me.py`**

```python
from fastapi import APIRouter, Depends, status

from src.domain.auth.entities import User
from src.presentation.api.v1.auth.dependencies import get_current_user, get_user_service
from src.presentation.api.v1.auth.schemas import (
    BindTelegramRequest,
    ResetPasswordRequest,
    UserResponse,
)
from src.presentation.api.v1.auth.service import UserService

router = APIRouter(prefix="/users/me", tags=["Me"])


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        roles=user.roles,
        is_active=user.is_active,
        telegram_username=user.telegram_username,
        telegram_id=user.telegram_id,
    )


@router.get("", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _to_response(current_user)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_my_password(
    body: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> None:
    await service.reset_password(current_user.id, body.old_password, body.new_password)


@router.post("/bind-telegram", status_code=status.HTTP_204_NO_CONTENT)
async def bind_my_telegram(
    body: BindTelegramRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> None:
    await service.bind_telegram(current_user.id, body.telegram_username)
```

- [ ] **Step 2: Register the router in `src/presentation/api/v1/__init__.py`**

Add after existing imports and `router.include_router(auth_router)`:

```python
from src.presentation.api.v1.auth import router as auth_router
from src.presentation.api.v1.auth.me import router as me_router
from src.presentation.api.v1.delivery import router as delivery_router
from src.presentation.api.v1.orders import router as orders_router
from src.presentation.api.v1.references import router as references_router
from src.presentation.api.v1.tasks import router as tasks_router
from src.presentation.api.v1.warehouse import router as warehouse_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(references_router)
router.include_router(auth_router)
router.include_router(me_router)
router.include_router(warehouse_router)
router.include_router(orders_router)
router.include_router(tasks_router)
router.include_router(delivery_router)
```

- [ ] **Step 3: Verify backend still starts**

```bash
uvicorn src.main:app --reload
# Open http://localhost:8000/docs
# Check that GET /api/v1/users/me appears under "Me" tag
# Check that all existing routes are still present
```

- [ ] **Step 4: Run existing tests to confirm nothing broke**

```bash
pytest tests/ -x -q
# Expected: all passing (710+)
```

- [ ] **Step 5: Commit**

```bash
git add src/presentation/api/v1/auth/me.py src/presentation/api/v1/__init__.py
git commit -m "feat(auth): add /users/me endpoints for all authenticated users"
```

---

## Task 2: API Client (`api_client.py`)

**Files:**
- Create: `src/presentation/streamlit/api_client.py`

- [ ] **Step 1: Create `src/presentation/streamlit/api_client.py`**

```python
import base64
import json
import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


class SessionExpiredError(Exception):
    pass


class APIError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class APIClient:
    def __init__(self, base_url: str, access_token: str, refresh_token: str) -> None:
        self._base_url = base_url
        self._access_token = access_token
        self._refresh_token = refresh_token

    def get(self, path: str, **params) -> dict | list:
        filtered = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", path, params=filtered).json()

    def post(self, path: str, body: dict | None = None) -> dict | None:
        resp = self._request("POST", path, json=body)
        if resp.status_code == 204:
            return None
        return resp.json()

    def patch(self, path: str, body: dict) -> dict | None:
        resp = self._request("PATCH", path, json=body)
        if resp.status_code == 204:
            return None
        return resp.json()

    def put(self, path: str, body: dict) -> dict | None:
        resp = self._request("PUT", path, json=body)
        if resp.status_code == 204:
            return None
        return resp.json()

    def delete(self, path: str) -> None:
        self._request("DELETE", path)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            new_tokens = self._try_refresh()
            if new_tokens is None:
                raise SessionExpiredError()
            self._access_token = new_tokens["access_token"]
            self._refresh_token = new_tokens["refresh_token"]
            st.session_state["tokens"] = new_tokens
            headers = {"Authorization": f"Bearer {self._access_token}"}
            with httpx.Client(timeout=10.0) as client:
                resp = client.request(method, url, headers=headers, **kwargs)
            if resp.status_code == 401:
                raise SessionExpiredError()

        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise APIError(resp.status_code, str(detail))

        return resp

    def _try_refresh(self) -> dict | None:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self._base_url}/auth/refresh",
                    json={"refresh_token": self._refresh_token},
                )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None


def decode_token_payload(token: str) -> dict:
    """Decode JWT payload (middle segment) without signature verification."""
    payload_b64 = token.split(".")[1]
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def get_client() -> APIClient:
    tokens = st.session_state.get("tokens")
    if not tokens:
        raise SessionExpiredError()
    return APIClient(
        base_url=API_BASE_URL,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/presentation/streamlit/api_client.py
git commit -m "feat(streamlit): add APIClient with token management"
```

---

## Task 3: Entry point (`app.py`)

**Files:**
- Create: `src/presentation/streamlit/app.py`

- [ ] **Step 1: Create `src/presentation/streamlit/app.py`**

```python
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
```

- [ ] **Step 2: Verify the app starts (login page visible)**

```bash
cd /path/to/project
streamlit run src/presentation/streamlit/app.py
# Open http://localhost:8501
# Expected: login form visible (no authenticated session)
```

- [ ] **Step 3: Commit**

```bash
git add src/presentation/streamlit/app.py
git commit -m "feat(streamlit): add app.py entry point with role-based navigation"
```

---

## Task 4: Login page

**Files:**
- Create: `src/presentation/streamlit/pages/login.py`

- [ ] **Step 1: Create `src/presentation/streamlit/pages/login.py`**

```python
import os

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
```

- [ ] **Step 2: Verify login works**

```bash
# With backend running, open http://localhost:8501
# Log in with a test user
# Expected: redirect to first available page after login
```

- [ ] **Step 3: Commit**

```bash
git add src/presentation/streamlit/pages/login.py
git commit -m "feat(streamlit): add login page"
```

---

## Task 5: References page

**Files:**
- Create: `src/presentation/streamlit/pages/references.py`

- [ ] **Step 1: Create `src/presentation/streamlit/pages/references.py`**

```python
import streamlit as st

from api_client import APIError, get_client

st.title("Справочники")

client = get_client()


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


tab_customers, tab_products, tab_raw, tab_packaging = st.tabs(
    ["Клиенты", "Товары", "Сырьё", "Упаковка"]
)

# ── Клиенты ──────────────────────────────────────────────────────────────────
with tab_customers:
    show_inactive = st.checkbox("Показать неактивных", key="cust_inactive")
    try:
        customers = client.get("/references/customers", include_inactive=show_inactive)
    except APIError as e:
        _err(e)
        customers = []

    for c in customers:
        status_icon = "🟢" if c["is_active"] else "🔴"
        with st.expander(f"{status_icon} {c['name']} (id={c['id']})"):
            st.write(f"Адрес: {c['default_address']}")
            col1, col2 = st.columns(2)
            if c["is_active"]:
                if col1.button("Деактивировать", key=f"cust_deact_{c['id']}"):
                    try:
                        client.post(f"/references/customers/{c['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if col1.button("Активировать", key=f"cust_act_{c['id']}"):
                    try:
                        client.post(f"/references/customers/{c['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Добавить клиента")
    with st.form("create_customer"):
        name = st.text_input("Название")
        address = st.text_input("Адрес по умолчанию")
        if st.form_submit_button("Создать"):
            try:
                client.post(
                    "/references/customers",
                    body={"name": name, "default_address": address},
                )
                st.success("Клиент создан")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Товары ────────────────────────────────────────────────────────────────────
with tab_products:
    show_inactive_p = st.checkbox("Показать неактивные", key="prod_inactive")
    try:
        products = client.get("/references/products", include_inactive=show_inactive_p)
        raw_materials_list = client.get("/references/raw-materials", include_inactive=False)
        rm_map = {rm["id"]: rm["name"] for rm in raw_materials_list}
    except APIError as e:
        _err(e)
        products = []
        rm_map = {}

    for p in products:
        status_icon = "🟢" if p["is_active"] else "🔴"
        with st.expander(f"{status_icon} {p['name']} (id={p['id']})"):
            st.write(
                f"Ед/упак: {p['units_per_box']} | "
                f"Срок хранения: {p['shelf_life_days']} дн. | "
                f"Крит. остаток: {p['critical_stock']}"
            )
            if p["is_active"]:
                if st.button("Деактивировать", key=f"prod_deact_{p['id']}"):
                    try:
                        client.post(f"/references/products/{p['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if st.button("Активировать", key=f"prod_act_{p['id']}"):
                    try:
                        client.post(f"/references/products/{p['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

            with st.expander("Рецептура", expanded=False):
                recipe = p.get("recipe", [])
                if recipe:
                    for line in recipe:
                        rm_name = rm_map.get(line["raw_material_id"], f"id={line['raw_material_id']}")
                        st.write(
                            f"- {rm_name}: {line['consumption_per_unit']} ед/шт, "
                            f"брак {line['waste_percentage']}%"
                        )
                else:
                    st.write("Рецептура не задана")

                st.write("**Заменить рецептуру:**")
                if rm_map:
                    n_lines = st.number_input(
                        "Количество строк", min_value=1, max_value=20, value=1,
                        key=f"recipe_n_{p['id']}",
                    )
                    recipe_lines = []
                    rm_ids = list(rm_map.keys())
                    for i in range(int(n_lines)):
                        c1, c2, c3 = st.columns(3)
                        rm_id = c1.selectbox(
                            "Сырьё", options=rm_ids,
                            format_func=lambda x: rm_map.get(x, x),
                            key=f"recipe_rm_{p['id']}_{i}",
                        )
                        consumption = c2.number_input(
                            "Расход (ед/шт)", min_value=0.001, value=1.0, step=0.001,
                            key=f"recipe_cons_{p['id']}_{i}",
                        )
                        waste = c3.number_input(
                            "Брак %", min_value=0.0, max_value=100.0, value=0.0,
                            key=f"recipe_waste_{p['id']}_{i}",
                        )
                        recipe_lines.append({
                            "raw_material_id": rm_id,
                            "consumption_per_unit": consumption,
                            "waste_percentage": waste,
                        })
                    if st.button("Сохранить рецептуру", key=f"recipe_save_{p['id']}"):
                        try:
                            client.put(
                                f"/references/products/{p['id']}/recipe",
                                body={"lines": recipe_lines},
                            )
                            st.success("Рецептура обновлена")
                            st.rerun()
                        except APIError as e:
                            _err(e)
                else:
                    st.info("Сначала добавьте сырьё в справочник.")

    st.divider()
    st.subheader("Добавить товар")
    with st.form("create_product"):
        name = st.text_input("Название")
        upb = st.number_input("Ед/упак", min_value=1, value=1)
        sld = st.number_input("Срок хранения (дни)", min_value=1, value=30)
        cs = st.number_input("Критический остаток", min_value=0, value=0)
        if st.form_submit_button("Создать"):
            try:
                client.post(
                    "/references/products",
                    body={
                        "name": name,
                        "units_per_box": upb,
                        "shelf_life_days": sld,
                        "critical_stock": cs,
                    },
                )
                st.success("Товар создан")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Сырьё ─────────────────────────────────────────────────────────────────────
with tab_raw:
    show_inactive_rm = st.checkbox("Показать неактивные", key="rm_inactive")
    try:
        rms = client.get("/references/raw-materials", include_inactive=show_inactive_rm)
    except APIError as e:
        _err(e)
        rms = []

    for rm in rms:
        status_icon = "🟢" if rm["is_active"] else "🔴"
        with st.expander(f"{status_icon} {rm['name']} ({rm['unit']}) (id={rm['id']})"):
            st.write(
                f"Срок хранения: {rm['shelf_life_days']} дн. | "
                f"Крит. остаток: {rm['critical_stock']}"
            )
            if rm["is_active"]:
                if st.button("Деактивировать", key=f"rm_deact_{rm['id']}"):
                    try:
                        client.post(f"/references/raw-materials/{rm['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if st.button("Активировать", key=f"rm_act_{rm['id']}"):
                    try:
                        client.post(f"/references/raw-materials/{rm['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Добавить сырьё")
    with st.form("create_rm"):
        name = st.text_input("Название")
        unit = st.text_input("Единица измерения", value="кг")
        sld = st.number_input("Срок хранения (дни)", min_value=1, value=30)
        cs = st.number_input("Критический остаток", min_value=0.0, value=0.0, step=0.1)
        if st.form_submit_button("Создать"):
            try:
                client.post(
                    "/references/raw-materials",
                    body={
                        "name": name,
                        "unit": unit,
                        "shelf_life_days": sld,
                        "critical_stock": cs,
                    },
                )
                st.success("Сырьё добавлено")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Упаковка ──────────────────────────────────────────────────────────────────
with tab_packaging:
    show_inactive_pk = st.checkbox("Показать неактивные", key="pk_inactive")
    try:
        packagings = client.get("/references/packaging", include_inactive=show_inactive_pk)
    except APIError as e:
        _err(e)
        packagings = []

    for pk in packagings:
        status_icon = "🟢" if pk["is_active"] else "🔴"
        with st.expander(f"{status_icon} {pk['name']} ({pk['unit']}) (id={pk['id']})"):
            st.write(f"Крит. остаток: {pk['critical_stock']}")
            if pk["is_active"]:
                if st.button("Деактивировать", key=f"pk_deact_{pk['id']}"):
                    try:
                        client.post(f"/references/packaging/{pk['id']}/deactivate")
                        st.rerun()
                    except APIError as e:
                        _err(e)
            else:
                if st.button("Активировать", key=f"pk_act_{pk['id']}"):
                    try:
                        client.post(f"/references/packaging/{pk['id']}/activate")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Добавить упаковку")
    with st.form("create_pk"):
        name = st.text_input("Название")
        unit = st.text_input("Единица", value="шт")
        cs = st.number_input("Критический остаток", min_value=0, value=0)
        if st.form_submit_button("Создать"):
            try:
                client.post(
                    "/references/packaging",
                    body={"name": name, "unit": unit, "critical_stock": cs},
                )
                st.success("Упаковка добавлена")
                st.rerun()
            except APIError as e:
                _err(e)
```

- [ ] **Step 2: Verify as director**

```bash
# Log in as director → navigate to "Справочники"
# Expected: 4 tabs (Клиенты, Товары, Сырьё, Упаковка)
# Create a customer → appears in list
# Deactivate/activate a record → status icon changes
# Set a recipe on a product → recipe lines appear
```

- [ ] **Step 3: Commit**

```bash
git add src/presentation/streamlit/pages/references.py
git commit -m "feat(streamlit): add references page (customers, products, raw materials, packaging)"
```

---

## Task 6: Orders page

**Files:**
- Create: `src/presentation/streamlit/pages/orders.py`

- [ ] **Step 1: Create `src/presentation/streamlit/pages/orders.py`**

```python
import streamlit as st

from api_client import APIError, get_client

st.title("Заказы")

client = get_client()


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load reference data ───────────────────────────────────────────────────────
try:
    customers = client.get("/references/customers", include_inactive=False)
    customer_map = {c["id"]: c["name"] for c in customers}
    products = client.get("/references/products", include_inactive=False)
    product_map = {p["id"]: p["name"] for p in products}
    users = client.get("/users")
    delivery_users = [u for u in users if "delivery" in u.get("roles", [])]
    delivery_user_map = {u["id"]: u["full_name"] for u in delivery_users}
except APIError as e:
    _err(e)
    customer_map = {}
    product_map = {}
    delivery_user_map = {}

# ── Filters ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
status_filter = col1.selectbox(
    "Статус",
    options=["", "new", "confirmed", "assembly", "delivery", "completed", "cancelled"],
    format_func=lambda x: x if x else "Все",
)
customer_filter_options = [""] + list(customer_map.keys())
customer_filter = col2.selectbox(
    "Клиент",
    options=customer_filter_options,
    format_func=lambda x: customer_map.get(x, "Все") if x else "Все",
)

# ── Order list ────────────────────────────────────────────────────────────────
try:
    orders = client.get(
        "/orders",
        status=status_filter if status_filter else None,
        customer_id=customer_filter if customer_filter else None,
    )
except APIError as e:
    _err(e)
    orders = []

for o in orders:
    cust_name = customer_map.get(o["customer_id"], f"id={o['customer_id']}")
    label = f"#{o['number']} — {cust_name} — {o['status']} — {o['delivery_date']}"
    with st.expander(label):
        st.write(f"Адрес: {o['delivery_address']}")
        if o.get("comment"):
            st.write(f"Комментарий: {o['comment']}")
        if o.get("delivery_user_id"):
            st.write(f"Водитель: {delivery_user_map.get(o['delivery_user_id'], o['delivery_user_id'])}")

        # Items
        try:
            items = client.get(f"/orders/{o['id']}/items")
        except APIError:
            items = []
        if items:
            st.write("**Позиции:**")
            for item in items:
                prod_name = product_map.get(item["product_id"], f"id={item['product_id']}")
                st.write(f"- {prod_name}: {item['quantity']} шт.")

        # Status change
        new_status = st.selectbox(
            "Сменить статус",
            options=["", "new", "confirmed", "assembly", "delivery", "completed", "cancelled"],
            format_func=lambda x: x if x else "— не менять —",
            key=f"order_status_{o['id']}",
        )
        if new_status and st.button("Применить статус", key=f"order_apply_status_{o['id']}"):
            try:
                client.patch(f"/orders/{o['id']}/status", body={"new_status": new_status})
                st.success("Статус изменён")
                st.rerun()
            except APIError as e:
                _err(e)

        # Delete
        if st.button("Удалить заказ", key=f"order_del_{o['id']}"):
            try:
                client.delete(f"/orders/{o['id']}")
                st.success("Заказ удалён")
                st.rerun()
            except APIError as e:
                _err(e)

# ── Create order ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("Создать заказ")

if not customer_map or not product_map:
    st.info("Для создания заказа необходимы клиенты и товары в справочниках.")
else:
    with st.form("create_order"):
        cust_id = st.selectbox(
            "Клиент",
            options=list(customer_map.keys()),
            format_func=lambda x: customer_map[x],
        )
        address = st.text_input("Адрес доставки")
        delivery_date = st.date_input("Дата доставки")
        comment = st.text_input("Комментарий", value="")

        driver_options = [None] + list(delivery_user_map.keys())
        driver_id = st.selectbox(
            "Водитель (необязательно)",
            options=driver_options,
            format_func=lambda x: delivery_user_map.get(x, "— не назначен —") if x else "— не назначен —",
        )

        st.write("**Позиции заказа:**")
        n_items = st.number_input("Количество позиций", min_value=1, max_value=50, value=1)
        items = []
        prod_ids = list(product_map.keys())
        for i in range(int(n_items)):
            c1, c2 = st.columns(2)
            pid = c1.selectbox(
                "Товар", options=prod_ids,
                format_func=lambda x: product_map.get(x, x),
                key=f"order_prod_{i}",
            )
            qty = c2.number_input("Кол-во", min_value=1, value=1, key=f"order_qty_{i}")
            items.append({"product_id": pid, "quantity": qty})

        if st.form_submit_button("Создать заказ"):
            try:
                client.post(
                    "/orders",
                    body={
                        "customer_id": cust_id,
                        "delivery_address": address,
                        "delivery_date": str(delivery_date),
                        "items": items,
                        "delivery_user_id": driver_id,
                        "comment": comment if comment else None,
                    },
                )
                st.success("Заказ создан")
                st.rerun()
            except APIError as e:
                _err(e)
```

- [ ] **Step 2: Verify as director**

```bash
# Navigate to "Заказы"
# Expected: filter bar, list of orders (if any), create form
# Create an order → it appears in the list
# Change status → status updates
```

- [ ] **Step 3: Commit**

```bash
git add src/presentation/streamlit/pages/orders.py
git commit -m "feat(streamlit): add orders page"
```

---

## Task 7: Tasks page

**Files:**
- Create: `src/presentation/streamlit/pages/tasks.py`

- [ ] **Step 1: Create `src/presentation/streamlit/pages/tasks.py`**

```python
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
```

- [ ] **Step 2: Verify**

```bash
# Log in as production user → see only own tasks, no create form
# Log in as director → see all tasks, create form, close/reassign/delete buttons
# Create a task → start → stop (with reason) → resume → complete (with consumptions)
# Director: close a completed task
```

- [ ] **Step 3: Commit**

```bash
git add src/presentation/streamlit/pages/tasks.py
git commit -m "feat(streamlit): add tasks page with full state machine"
```

---

## Task 8: Warehouse page

**Files:**
- Create: `src/presentation/streamlit/pages/warehouse.py`

- [ ] **Step 1: Create `src/presentation/streamlit/pages/warehouse.py`**

```python
import streamlit as st

from api_client import APIError, get_client

st.title("Склад")

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load reference data ───────────────────────────────────────────────────────
try:
    raw_materials_list = client.get("/references/raw-materials", include_inactive=False)
    rm_map = {rm["id"]: f"{rm['name']} ({rm['unit']})" for rm in raw_materials_list}
    packaging_list = client.get("/references/packaging", include_inactive=False)
    pkg_map = {p["id"]: f"{p['name']} ({p['unit']})" for p in packaging_list}
    products = client.get("/references/products", include_inactive=False)
    prod_map = {p["id"]: p["name"] for p in products}
except APIError as e:
    _err(e)
    rm_map = {}
    pkg_map = {}
    prod_map = {}

tab_raw, tab_pkg, tab_prod = st.tabs(["Сырьё", "Упаковка", "Продукция"])

# ── Сырьё ─────────────────────────────────────────────────────────────────────
with tab_raw:
    rm_filter_options = [None] + list(rm_map.keys())
    rm_filter = st.selectbox(
        "Фильтр по сырью",
        options=rm_filter_options,
        format_func=lambda x: rm_map.get(x, "Все") if x else "Все",
        key="wh_rm_filter",
    )
    try:
        raw_stocks = client.get(
            "/warehouse/raw-material-stock",
            raw_material_id=rm_filter,
        )
    except APIError as e:
        _err(e)
        raw_stocks = []

    for s in raw_stocks:
        rm_name = rm_map.get(s["raw_material_id"], f"id={s['raw_material_id']}")
        with st.expander(f"{rm_name} — {s['quantity']} ед. (id={s['id']})"):
            st.write(f"Приход: {s['arrival_date']} | Истекает: {s['expiry_date']}")
            if s.get("comment"):
                st.write(f"Комментарий: {s['comment']}")
            with st.form(f"rm_writeoff_{s['id']}"):
                amount = st.number_input(
                    "Списать (ед.)", min_value=0.001, step=0.001, value=0.001,
                    key=f"rm_wo_amount_{s['id']}",
                )
                if st.form_submit_button("Списать"):
                    try:
                        client.post(
                            f"/warehouse/raw-material-stock/{s['id']}/write-off",
                            body={"amount": amount},
                        )
                        st.success("Списано")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Приход сырья")
    if not rm_map:
        st.info("Сначала добавьте сырьё в справочник.")
    else:
        with st.form("rm_arrival"):
            rm_id = st.selectbox(
                "Сырьё", options=list(rm_map.keys()),
                format_func=lambda x: rm_map[x],
            )
            quantity = st.number_input("Количество", min_value=0.001, step=0.001, value=1.0)
            arrival_date = st.date_input("Дата прихода")
            expiry_date = st.date_input("Дата истечения")
            comment = st.text_input("Комментарий")
            if st.form_submit_button("Оприходовать"):
                try:
                    client.post(
                        "/warehouse/raw-material-stock",
                        body={
                            "raw_material_id": rm_id,
                            "quantity": quantity,
                            "arrival_date": str(arrival_date),
                            "expiry_date": str(expiry_date),
                            "comment": comment if comment else None,
                        },
                    )
                    st.success("Приход зарегистрирован")
                    st.rerun()
                except APIError as e:
                    _err(e)

# ── Упаковка ──────────────────────────────────────────────────────────────────
with tab_pkg:
    pkg_filter_options = [None] + list(pkg_map.keys())
    pkg_filter = st.selectbox(
        "Фильтр по упаковке",
        options=pkg_filter_options,
        format_func=lambda x: pkg_map.get(x, "Все") if x else "Все",
        key="wh_pkg_filter",
    )
    try:
        pkg_stocks = client.get(
            "/warehouse/packaging-stock",
            packaging_id=pkg_filter,
        )
    except APIError as e:
        _err(e)
        pkg_stocks = []

    for s in pkg_stocks:
        pkg_name = pkg_map.get(s["packaging_id"], f"id={s['packaging_id']}")
        with st.expander(f"{pkg_name} — {s['quantity']} шт. (id={s['id']})"):
            if s.get("comment"):
                st.write(f"Комментарий: {s['comment']}")
            with st.form(f"pkg_writeoff_{s['id']}"):
                amount = st.number_input(
                    "Списать (шт.)", min_value=1, value=1,
                    key=f"pkg_wo_amount_{s['id']}",
                )
                if st.form_submit_button("Списать"):
                    try:
                        client.post(
                            f"/warehouse/packaging-stock/{s['id']}/write-off",
                            body={"amount": amount},
                        )
                        st.success("Списано")
                        st.rerun()
                    except APIError as e:
                        _err(e)

    st.divider()
    st.subheader("Приход упаковки")
    if not pkg_map:
        st.info("Сначала добавьте упаковку в справочник.")
    else:
        with st.form("pkg_arrival"):
            pkg_id = st.selectbox(
                "Упаковка", options=list(pkg_map.keys()),
                format_func=lambda x: pkg_map[x],
            )
            quantity = st.number_input("Количество (шт.)", min_value=1, value=1)
            comment = st.text_input("Комментарий")
            if st.form_submit_button("Оприходовать"):
                try:
                    client.post(
                        "/warehouse/packaging-stock",
                        body={
                            "packaging_id": pkg_id,
                            "quantity": quantity,
                            "comment": comment if comment else None,
                        },
                    )
                    st.success("Приход зарегистрирован")
                    st.rerun()
                except APIError as e:
                    _err(e)

# ── Продукция ─────────────────────────────────────────────────────────────────
with tab_prod:
    prod_filter_options = [None] + list(prod_map.keys())
    prod_filter = st.selectbox(
        "Фильтр по товару",
        options=prod_filter_options,
        format_func=lambda x: prod_map.get(x, "Все") if x else "Все",
        key="wh_prod_filter",
    )
    try:
        prod_stocks = client.get(
            "/warehouse/product-stock",
            product_id=prod_filter,
        )
    except APIError as e:
        _err(e)
        prod_stocks = []

    for s in prod_stocks:
        prod_name = prod_map.get(s["product_id"], f"id={s['product_id']}")
        with st.expander(
            f"{prod_name} — {s['quantity']} шт. | "
            f"Партия {s['batch_number']}/{s['batch_year']} | "
            f"до {s['expiry_date']} (id={s['id']})"
        ):
            st.write(f"Приход: {s['arrival_date']}")
            if s.get("comment"):
                st.write(f"Комментарий: {s['comment']}")
            if is_director:
                with st.form(f"prod_writeoff_{s['id']}"):
                    amount = st.number_input(
                        "Списать (шт.)", min_value=1, value=1,
                        key=f"prod_wo_amount_{s['id']}",
                    )
                    if st.form_submit_button("Списать (директор)"):
                        try:
                            client.post(
                                f"/warehouse/product-stock/{s['id']}/write-off",
                                body={"amount": amount},
                            )
                            st.success("Списано")
                            st.rerun()
                        except APIError as e:
                            _err(e)

    st.divider()
    st.subheader("Приход продукции")
    if not prod_map:
        st.info("Сначала добавьте товары в справочник.")
    else:
        with st.form("prod_arrival"):
            prod_id = st.selectbox(
                "Товар", options=list(prod_map.keys()),
                format_func=lambda x: prod_map[x],
            )
            quantity = st.number_input("Количество (шт.)", min_value=1, value=1)
            arrival_date = st.date_input("Дата прихода")
            expiry_date = st.date_input("Дата истечения")
            comment = st.text_input("Комментарий")
            if st.form_submit_button("Оприходовать"):
                try:
                    client.post(
                        "/warehouse/product-stock",
                        body={
                            "product_id": prod_id,
                            "quantity": quantity,
                            "arrival_date": str(arrival_date),
                            "expiry_date": str(expiry_date),
                            "comment": comment if comment else None,
                        },
                    )
                    st.success("Приход зарегистрирован")
                    st.rerun()
                except APIError as e:
                    _err(e)
```

- [ ] **Step 2: Verify**

```bash
# Log in as warehouse → see all 3 tabs, no product write-off button
# Log in as director → product write-off button visible
# Register arrival → appears in list
# Write off → quantity updates after rerun
```

- [ ] **Step 3: Commit**

```bash
git add src/presentation/streamlit/pages/warehouse.py
git commit -m "feat(streamlit): add warehouse page (raw materials, packaging, products)"
```

---

## Task 9: Deliveries page

**Files:**
- Create: `src/presentation/streamlit/pages/deliveries.py`

- [ ] **Step 1: Create `src/presentation/streamlit/pages/deliveries.py`**

```python
import streamlit as st

from api_client import APIError, get_client

st.title("Доставки")

client = get_client()
roles = st.session_state.get("roles", [])
is_director = "director" in roles


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load reference data ───────────────────────────────────────────────────────
try:
    if is_director:
        users = client.get("/users")
        delivery_users = [u for u in users if "delivery" in u.get("roles", [])]
        delivery_user_map = {u["id"]: u["full_name"] for u in delivery_users}
    else:
        delivery_user_map = {}
except APIError as e:
    _err(e)
    delivery_user_map = {}

# ── Filters ───────────────────────────────────────────────────────────────────
status_filter = st.selectbox(
    "Статус",
    options=["", "pending", "picked_up", "in_transit", "completed", "cancelled"],
    format_func=lambda x: x if x else "Все",
)

# ── Delivery list ─────────────────────────────────────────────────────────────
try:
    deliveries = client.get(
        "/deliveries",
        status=status_filter if status_filter else None,
    )
except APIError as e:
    _err(e)
    deliveries = []

for d in deliveries:
    executor_name = delivery_user_map.get(d["executor_id"], f"id={d['executor_id']}")
    label = (
        f"Заказ #{d['order_id']} — {d['status']} — "
        f"{d['planned_date']} — {executor_name}"
    )
    with st.expander(label):
        if d.get("started_at"):
            st.write(f"Выехал: {d['started_at']}")
        if d.get("completed_at"):
            st.write(f"Завершена: {d['completed_at']}")
        if d.get("cancellation_reason"):
            st.write(f"Причина отмены: {d['cancellation_reason']}")

        s = d["status"]

        if s == "pending":
            col1, col2 = st.columns(2)
            if col1.button("Принять", key=f"del_pickup_{d['id']}"):
                try:
                    client.post(f"/deliveries/{d['id']}/pick-up")
                    st.rerun()
                except APIError as e:
                    _err(e)
            if col2.button("Отменить", key=f"del_cancel_btn_{d['id']}"):
                st.session_state[f"del_cancel_open_{d['id']}"] = True
            if st.session_state.get(f"del_cancel_open_{d['id']}"):
                with st.form(f"del_cancel_form_{d['id']}"):
                    reason = st.text_input("Причина отмены")
                    if st.form_submit_button("Подтвердить"):
                        try:
                            client.post(
                                f"/deliveries/{d['id']}/cancel",
                                body={"reason": reason},
                            )
                            st.session_state.pop(f"del_cancel_open_{d['id']}", None)
                            st.rerun()
                        except APIError as e:
                            _err(e)

        elif s == "picked_up":
            col1, col2 = st.columns(2)
            if col1.button("Выехал", key=f"del_start_{d['id']}"):
                try:
                    client.post(f"/deliveries/{d['id']}/start")
                    st.rerun()
                except APIError as e:
                    _err(e)
            if col2.button("Отменить", key=f"del_cancel_btn2_{d['id']}"):
                st.session_state[f"del_cancel_open2_{d['id']}"] = True
            if st.session_state.get(f"del_cancel_open2_{d['id']}"):
                with st.form(f"del_cancel_form2_{d['id']}"):
                    reason = st.text_input("Причина отмены")
                    if st.form_submit_button("Подтвердить"):
                        try:
                            client.post(
                                f"/deliveries/{d['id']}/cancel",
                                body={"reason": reason},
                            )
                            st.session_state.pop(f"del_cancel_open2_{d['id']}", None)
                            st.rerun()
                        except APIError as e:
                            _err(e)

        elif s == "in_transit":
            if st.button("Завершить доставку", key=f"del_complete_{d['id']}"):
                try:
                    client.post(f"/deliveries/{d['id']}/complete")
                    st.rerun()
                except APIError as e:
                    _err(e)

# ── Create delivery (director only) ──────────────────────────────────────────
if is_director:
    st.divider()
    st.subheader("Создать доставку")
    if not delivery_user_map:
        st.info("Нет водителей (пользователей с ролью delivery).")
    else:
        with st.form("create_delivery"):
            order_id = st.number_input("ID заказа", min_value=1, value=1)
            executor_id = st.selectbox(
                "Водитель",
                options=list(delivery_user_map.keys()),
                format_func=lambda x: delivery_user_map[x],
            )
            planned_date = st.date_input("Плановая дата")
            if st.form_submit_button("Создать"):
                try:
                    client.post(
                        "/deliveries",
                        body={
                            "order_id": order_id,
                            "executor_id": executor_id,
                            "planned_date": str(planned_date),
                        },
                    )
                    st.success("Доставка создана")
                    st.rerun()
                except APIError as e:
                    _err(e)
```

- [ ] **Step 2: Verify**

```bash
# Log in as delivery → see own deliveries, pending pickup
# Pick up → status becomes picked_up
# Start → in_transit
# Complete → completed
# Log in as director → see all, create delivery form
```

- [ ] **Step 3: Commit**

```bash
git add src/presentation/streamlit/pages/deliveries.py
git commit -m "feat(streamlit): add deliveries page"
```

---

## Task 10: Settings page

**Files:**
- Create: `src/presentation/streamlit/pages/settings.py`

- [ ] **Step 1: Create `src/presentation/streamlit/pages/settings.py`**

```python
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
```

- [ ] **Step 2: Verify**

```bash
# All roles: see own info, change password form, telegram form
# Director: additionally see user list and create form
# Change password → success message
# Create a new user → appears in list
# Set roles → roles update
```

- [ ] **Step 3: Commit**

```bash
git add src/presentation/streamlit/pages/settings.py
git commit -m "feat(streamlit): add settings page (password, telegram, user management)"
```

---

## Task 11: Update roadmap + commit spec/plan + merge

- [ ] **Step 1: Update `docs/roadmap.md` — mark Phase 9 items as done**

In `docs/roadmap.md`, replace the Phase 9 section:

```markdown
## Phase 9 — Streamlit prototype ✅
> Ветка: `feature/streamlit` → влита в `develop`

- [x] Авторизация (login форма)
- [x] Страница справочников
- [x] Страница заказов
- [x] Страница производственных задач
- [x] Страница склада
- [x] Страница доставок
- [x] Страница настроек (смена пароля, Telegram, управление пользователями)
- [ ] Дашборд директора (Phase 8 dependency — не реализован)
```

- [ ] **Step 2: Commit roadmap and docs**

```bash
git add docs/roadmap.md docs/superpowers/specs/2026-05-17-streamlit-prototype-design.md docs/superpowers/plans/2026-05-17-streamlit-prototype.md
git commit -m "docs: mark Phase 9 Streamlit prototype as complete"
```

- [ ] **Step 3: Run all backend tests before merge**

```bash
pytest tests/ -x -q
# Expected: all passing
```

- [ ] **Step 4: Merge to develop**

```bash
git checkout develop
git merge --no-ff feature/streamlit -m "feat(streamlit): Phase 9 — Streamlit prototype (login, references, orders, tasks, warehouse, deliveries, settings)"
```

---

## Self-Review Notes

**Spec coverage check:**
- ✅ Login page — Task 4
- ✅ References (4 tabs, CRUD, recipe) — Task 5
- ✅ Orders (filter, create, status change, delete) — Task 6
- ✅ Tasks (full state machine, director extras) — Task 7
- ✅ Warehouse (3 tabs, arrival, write-off) — Task 8
- ✅ Deliveries (state machine, create) — Task 9
- ✅ Settings (password, telegram, user management) — Task 10
- ✅ `/users/me` backend addition — Task 1 (required by settings for non-directors)
- ✅ Role-based navigation — Task 3 (app.py)
- ✅ Token auto-refresh — Task 2 (api_client.py)
- ✅ SessionExpiredError handling — Task 3 (app.py catches, clears session)
- ✅ APIError display — every page catches and shows st.error()

**Type/naming consistency:**
- `APIClient.get()` → returns `dict | list` — used as `list` for collections, `dict` for single items
- `get_client()` → returns `APIClient` — used in every page
- `decode_token_payload()` → used in login.py only
- `SessionExpiredError`, `APIError` — imported consistently from `api_client`
- API paths: `/references/customers`, `/references/products`, `/references/raw-materials`, `/references/packaging`, `/warehouse/raw-material-stock`, `/warehouse/packaging-stock`, `/warehouse/product-stock`, `/orders`, `/tasks`, `/deliveries`, `/users`, `/users/me`, `/auth/*`

**No placeholders found.**
