import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.application.auth.dto import TokenPairDTO
from src.application.auth.exceptions import AuthenticationError, InvalidTokenError, RateLimitError
from src.application.references.exceptions import NotFoundError
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.presentation.api.v1.auth.dependencies import (
    get_auth_service,
    get_current_user,
    get_user_service,
)


# ---------------------------------------------------------------------------
# Fake services
# ---------------------------------------------------------------------------


class FakeAuthService:
    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}  # refresh_token → access_token
        self._failed: dict[str, int] = {}
        self._valid_users: dict[str, str] = {}  # username → password

    def add_user(self, username: str, password: str) -> None:
        self._valid_users[username] = password

    async def login(self, username: str, password: str) -> TokenPairDTO:
        if self._failed.get(username, 0) >= 5:
            raise RateLimitError(username)
        if self._valid_users.get(username) != password:
            self._failed[username] = self._failed.get(username, 0) + 1
            raise AuthenticationError()
        refresh = f"refresh-{username}"
        access = f"access-{username}"
        self._tokens[refresh] = access
        return TokenPairDTO(access_token=access, refresh_token=refresh)

    async def refresh_tokens(self, refresh_token: str) -> TokenPairDTO:
        if refresh_token not in self._tokens:
            raise InvalidTokenError()
        del self._tokens[refresh_token]
        new_refresh = f"{refresh_token}-new"
        new_access = f"access-new"
        self._tokens[new_refresh] = new_access
        return TokenPairDTO(access_token=new_access, refresh_token=new_refresh)

    async def logout(self, refresh_token: str) -> None:
        self._tokens.pop(refresh_token, None)


class FakeUserService:
    def __init__(self) -> None:
        self._store: dict[int, User] = {}
        self._next_id = 1

    async def get(self, id: int) -> User:
        user = self._store.get(id)
        if user is None:
            raise NotFoundError("User", id)
        return user

    async def get_all(self, include_inactive: bool = False) -> list[User]:
        users = list(self._store.values())
        return users if include_inactive else [u for u in users if u.is_active]

    async def create(self, full_name: str, password: str) -> int:
        user = User(username=f"user_{self._next_id}", full_name=full_name, id=self._next_id)
        self._store[self._next_id] = user
        self._next_id += 1
        return user.id

    async def update(self, id: int, full_name: str) -> None:
        (await self.get(id)).full_name = full_name

    async def set_roles(self, id: int, roles: list[Role]) -> None:
        user = await self.get(id)
        user.roles = list(roles)

    async def deactivate(self, id: int) -> None:
        (await self.get(id)).deactivate()

    async def activate(self, id: int) -> None:
        (await self.get(id)).activate()

    async def bind_telegram(self, id: int, telegram_username: str) -> None:
        (await self.get(id)).set_telegram_username(telegram_username)

    async def reset_password(self, id: int, old_password: str, new_password: str) -> None:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_svc() -> FakeAuthService:
    svc = FakeAuthService()
    svc.add_user("ivanov_ivan", "secret123")
    return svc


@pytest.fixture
def user_svc() -> FakeUserService:
    return FakeUserService()


def _make_director() -> User:
    u = User(username="director", full_name="Директор Директорович", id=1)
    u.add_role(Role.director)
    return u


def _make_warehouse() -> User:
    u = User(username="warehouse", full_name="Склад Складович", id=2)
    u.add_role(Role.warehouse)
    return u


@pytest_asyncio.fixture
async def client(auth_svc, user_svc) -> AsyncClient:
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    app.dependency_overrides[get_user_service] = lambda: user_svc
    app.dependency_overrides[get_current_user] = lambda: _make_director()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_warehouse(auth_svc, user_svc) -> AsyncClient:
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    app.dependency_overrides[get_user_service] = lambda: user_svc
    app.dependency_overrides[get_current_user] = lambda: _make_warehouse()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_no_auth(auth_svc, user_svc) -> AsyncClient:
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    app.dependency_overrides[get_user_service] = lambda: user_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
