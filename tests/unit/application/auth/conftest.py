import pytest

from src.application.ports.auth import (
    IAuthLogRepository,
    IJWTService,
    IPasswordHasher,
    IRefreshTokenRepository,
    IUserCredentialRepository,
    RefreshTokenData,
)
from src.domain.auth.entities import User
from src.domain.auth.interfaces import IUserRepository
from src.domain.auth.value_objects import Role


# ---------------------------------------------------------------------------
# Fake repositories
# ---------------------------------------------------------------------------


class FakeUserRepository(IUserRepository):
    def __init__(self) -> None:
        self._store: dict[int, User] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> User | None:
        return self._store.get(id)

    async def get_all(self, include_inactive: bool = False) -> list[User]:
        items = list(self._store.values())
        return items if include_inactive else [u for u in items if u.is_active]

    async def save(self, entity: User) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_by_username(self, username: str) -> User | None:
        return next((u for u in self._store.values() if u.username == username), None)

    async def exists_by_username(self, username: str, exclude_id: int | None = None) -> bool:
        return any(
            u.username == username and u.id != exclude_id
            for u in self._store.values()
        )


class FakeCredentialRepository(IUserCredentialRepository):
    def __init__(self) -> None:
        self._store: dict[int, str] = {}

    async def get_hashed_password(self, user_id: int) -> str | None:
        return self._store.get(user_id)

    async def save(self, user_id: int, hashed_password: str) -> None:
        self._store[user_id] = hashed_password

    async def update_password(self, user_id: int, hashed_password: str) -> None:
        self._store[user_id] = hashed_password


class FakeRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self) -> None:
        self._store: dict[str, int] = {}  # token -> user_id

    async def save(self, user_id: int, token: str) -> None:
        self._store[token] = user_id

    async def get_by_token(self, token: str) -> RefreshTokenData | None:
        user_id = self._store.get(token)
        return RefreshTokenData(user_id=user_id) if user_id is not None else None

    async def revoke(self, token: str) -> None:
        self._store.pop(token, None)

    async def revoke_all_for_user(self, user_id: int) -> None:
        self._store = {t: uid for t, uid in self._store.items() if uid != user_id}


class FakeAuthLogRepository(IAuthLogRepository):
    def __init__(self, failed_count: int = 0) -> None:
        self._failed_count = failed_count
        self.logged: list[tuple[str, int | None, bool]] = []

    async def log_attempt(self, username_attempt: str, user_id: int | None, success: bool) -> None:
        self.logged.append((username_attempt, user_id, success))

    async def count_failed_recent(self, username: str, window_seconds: int = 900) -> int:
        return self._failed_count


# ---------------------------------------------------------------------------
# Fake security services
# ---------------------------------------------------------------------------


class FakeHasher(IPasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


class FakeJWTService(IJWTService):
    def create_access_token(self, user_id: int, roles: list[str]) -> str:
        return f"token:{user_id}:{','.join(roles)}"

    def decode_access_token(self, token: str) -> dict:
        _, user_id, roles_str = token.split(":", 2)
        return {"sub": user_id, "roles": roles_str.split(",") if roles_str else []}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def cred_repo() -> FakeCredentialRepository:
    return FakeCredentialRepository()


@pytest.fixture
def token_repo() -> FakeRefreshTokenRepository:
    return FakeRefreshTokenRepository()


@pytest.fixture
def auth_log_repo() -> FakeAuthLogRepository:
    return FakeAuthLogRepository()


@pytest.fixture
def hasher() -> FakeHasher:
    return FakeHasher()


@pytest.fixture
def jwt_svc() -> FakeJWTService:
    return FakeJWTService()


@pytest.fixture
async def saved_user(user_repo, cred_repo, hasher) -> User:
    user = User(username="ivan_petrov", full_name="Иван Петров", roles=[Role.director])
    await user_repo.save(user)
    await cred_repo.save(user.id, hasher.hash("secret"))
    return user
