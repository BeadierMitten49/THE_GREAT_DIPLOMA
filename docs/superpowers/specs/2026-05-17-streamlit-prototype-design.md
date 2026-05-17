# Design: Streamlit Prototype (Phase 9)

**Date:** 2026-05-17
**Scope:** All pages except Director Dashboard (Phase 8 dependency)

---

## Overview

Streamlit prototype communicates with the FastAPI backend via HTTP. All data
comes from `/api/v1/*` endpoints. No direct database access from Streamlit.

Streamlit is a prototype UI, not a production interface.

---

## File Structure

```
src/presentation/streamlit/
├── app.py              # entry point: auth gate + st.navigation()
├── api_client.py       # httpx wrapper with token management
└── pages/
    ├── login.py
    ├── references.py
    ├── orders.py
    ├── tasks.py
    ├── warehouse.py
    ├── deliveries.py
    └── settings.py
```

Run with: `streamlit run src/presentation/streamlit/app.py`

---

## Architecture

### Navigation (`app.py`)

`app.py` is the single entry point. On every run it checks
`st.session_state["tokens"]`:

- **No tokens** → navigation contains only `login.py`, switch to it immediately.
- **Tokens present** → read `st.session_state["role"]`, build page list by role,
  call `st.navigation(pages).run()`.

Page list per role (union for multi-role users):

| Role | Pages |
|------|-------|
| director | References, Orders, Tasks, Warehouse, Deliveries, Settings |
| warehouse | Warehouse, Settings |
| production | Tasks, Settings |
| delivery | Deliveries, Settings |

A logout button in the sidebar clears `session_state` and calls `st.rerun()`.

### Auth Flow

1. User opens the app → no tokens → `login.py` shown.
2. `login.py`: username + password form → `POST /auth/login`.
3. On success: store `access_token`, `refresh_token`, `roles` in `session_state` → `st.rerun()`.
4. On 401: show "Неверный логин или пароль". On 429: show "Аккаунт заблокирован".
5. Every API call adds `Authorization: Bearer <access_token>`.
6. On 401 from any endpoint → attempt `POST /auth/refresh` once.
   - Success: store new tokens, retry original request.
   - Failure: clear `session_state`, `st.rerun()` (back to login).
7. Logout button → `POST /auth/logout` → clear `session_state` → `st.rerun()`.

---

## API Client (`api_client.py`)

Synchronous `httpx.Client` wrapper (Streamlit runs synchronously).

```python
class APIClient:
    def __init__(self, base_url: str, access_token: str, refresh_token: str)

    def get(self, path: str, **params) -> dict | list
    def post(self, path: str, body: dict | None = None) -> dict | None
    def patch(self, path: str, body: dict) -> dict | None
    def put(self, path: str, body: dict) -> dict | None
    def delete(self, path: str) -> None

    def _request(self, method, path, **kwargs) -> httpx.Response
    # On 401 → refresh once → retry
    # On repeated 401 → raise SessionExpiredError
    # On other 4xx/5xx → raise APIError(status_code, detail)

class SessionExpiredError(Exception): ...
class APIError(Exception):
    def __init__(self, status_code: int, detail: str)
```

`base_url` from env var `API_BASE_URL`, default `http://localhost:8000/api/v1`.

Helper `get_client() -> APIClient` reads tokens from `st.session_state`.

`SessionExpiredError` is caught in `app.py`, clears session, calls `st.rerun()`.
`APIError` is caught per-page and shown via `st.error(e.detail)`.

---

## Pages

### `login.py`

- Username + password inputs, «Войти» button.
- Calls `POST /auth/login`.
- Stores `access_token`, `refresh_token`, `roles` in `session_state`.
- Shows `st.error()` on 401 and 429.

### `references.py` (director only)

Four `st.tabs()`: Клиенты, Товары, Сырьё, Упаковка.

Each tab:
- Table of records (active only by default; checkbox «Показать неактивные»).
- Form to create a new record.
- Per-row buttons: Деактивировать / Активировать.

**Товары** tab additionally:
- Expander «Рецептура» per product row — shows current recipe ingredients
  and a form to replace the recipe (`POST /products/{id}/recipe`).

### `orders.py` (director only)

- Filter bar: статус (select), клиент (select).
- Table of orders.
- Form «Создать заказ»: клиент, адрес доставки, дата, позиции (product + qty,
  dynamic rows), ответственный водитель, комментарий.
- Per-row expander:
  - Order items list.
  - Status change: `PATCH /orders/{id}/status`.
  - Edit order: `PUT /orders/{id}`.
  - Delete: `DELETE /orders/{id}`.

### `tasks.py` (director + production)

- Filter: статус.
- Table of tasks (production role sees only own tasks — enforced by API).
- Per-row action buttons based on current status:
  - `pending` → «Старт»
  - `in_progress` → «Стоп» (reason input), «Завершить» (form: actual qty,
    consumptions per raw material, comment)
  - `stopped` → «Возобновить»
  - `completed` → «Закрыть» (director only)
- Director additional controls:
  - Form «Создать задачу».
  - «Переназначить» button with executor select.
  - «Удалить» button.

### `warehouse.py` (director + warehouse)

Three `st.tabs()`: Сырьё, Упаковка, Продукция.

Each tab:
- Filter by material/product (select box).
- Table of stock entries.
- Form «Приход»: material/product select, quantity, dates, comment.
- Per-row «Списать» button with quantity input.

### `deliveries.py` (director + delivery)

- Filter: статус.
- Table of deliveries (delivery role sees only own — enforced by API).
- Director: form «Создать доставку» (order, executor, planned date).
- Per-row action buttons based on status:
  - `pending` → «Принять», «Отменить» (reason input)
  - `picked_up` → «Старт», «Отменить» (reason input)
  - `in_transit` → «Завершить»

### `settings.py` (all roles)

**Section 1 — Сменить пароль** (all roles):
- Old password + new password inputs, «Сохранить» button.
- Calls `POST /auth/reset-password`.

**Section 2 — Telegram** (all roles):
- Telegram username input, «Привязать» button.
- Calls `PATCH /users/{id}/telegram`.

**Section 3 — Пользователи** (director only):
- Table of all users with roles and status.
- Form «Создать пользователя»: full name, username (auto or manual), password,
  roles (multiselect).
- Per-row: «Назначить роли» (multiselect + save), «Деактивировать» /
  «Активировать».

---

## Error Handling

| Error | Handling |
|-------|----------|
| `SessionExpiredError` | `app.py` catches, clears session, `st.rerun()` |
| `APIError` 4xx | Page catches, `st.error(detail)` |
| `APIError` 5xx | Page catches, `st.error("Ошибка сервера")` |
| Network error | Page catches `httpx.RequestError`, `st.error("Нет связи с сервером")` |

---

## Configuration

Single env var: `API_BASE_URL` (default: `http://localhost:8000/api/v1`).

No Streamlit config files needed beyond standard `.streamlit/config.toml` if
the user wants to change theme/port.

---

## Out of Scope

- Director Dashboard (Phase 8 dependency — not yet implemented).
- Tests (Streamlit prototype is explicitly not tested per roadmap).
- Production deployment concerns (Phase 10).
