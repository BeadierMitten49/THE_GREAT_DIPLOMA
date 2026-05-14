from abc import ABC, abstractmethod


class IRepository[T](ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> T | None: ...

    @abstractmethod
    async def get_all(self, include_inactive: bool = False) -> list[T]: ...

    @abstractmethod
    async def save(self, entity: T) -> int: ...
