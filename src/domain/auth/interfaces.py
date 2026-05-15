from abc import abstractmethod

from src.domain.auth.entities import User
from src.domain.shared.repository import ISoftDeleteRepository


class IUserRepository(ISoftDeleteRepository[User]):
    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def exists_by_username(self, username: str, exclude_id: int | None = None) -> bool: ...
