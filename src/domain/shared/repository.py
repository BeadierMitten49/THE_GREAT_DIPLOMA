from abc import ABC, abstractmethod


class IRepository[T](ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> T | None: ...

    @abstractmethod
    async def save(self, entity: T) -> int: ...


class ISoftDeleteRepository[T](IRepository[T]):
    @abstractmethod
    async def get_all(self, include_inactive: bool = False) -> list[T]: ...


class IPlainRepository[T](IRepository[T]):
    @abstractmethod
    async def get_all(self) -> list[T]: ...
