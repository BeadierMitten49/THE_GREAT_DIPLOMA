from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RefreshTokenData:
    user_id: int


class IUserCredentialRepository(ABC):
    @abstractmethod
    async def get_hashed_password(self, user_id: int) -> str | None: ...

    @abstractmethod
    async def save(self, user_id: int, hashed_password: str) -> None: ...

    @abstractmethod
    async def update_password(self, user_id: int, hashed_password: str) -> None: ...


class IRefreshTokenRepository(ABC):
    @abstractmethod
    async def save(self, user_id: int, token: str) -> None: ...

    @abstractmethod
    async def get_by_token(self, token: str) -> RefreshTokenData | None: ...

    @abstractmethod
    async def revoke(self, token: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: int) -> None: ...


class IAuthLogRepository(ABC):
    @abstractmethod
    async def log_attempt(
        self,
        username_attempt: str,
        user_id: int | None,
        success: bool,
    ) -> None: ...

    @abstractmethod
    async def count_failed_recent(self, username: str, window_seconds: int = 900) -> int: ...


class IPasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool: ...


class IJWTService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: int, roles: list[str]) -> str: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> dict: ...
