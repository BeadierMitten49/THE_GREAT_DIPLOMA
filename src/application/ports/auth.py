from abc import ABC, abstractmethod


class IUserCredentialRepository(ABC):
    @abstractmethod
    async def get_hashed_password(self, user_id: int) -> str | None: ...

    @abstractmethod
    async def save(self, user_id: int, hashed_password: str) -> None: ...

    @abstractmethod
    async def update_password(self, user_id: int, hashed_password: str) -> None: ...
