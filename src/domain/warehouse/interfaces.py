from abc import ABC, abstractmethod

from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock


class IStockRepository[T](ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> T | None: ...

    @abstractmethod
    async def get_all(self) -> list[T]: ...

    @abstractmethod
    async def save(self, entity: T) -> int: ...


class IRawMaterialStockRepository(IStockRepository[RawMaterialStock]):
    @abstractmethod
    async def get_by_raw_material(self, raw_material_id: int) -> list[RawMaterialStock]: ...


class IPackagingStockRepository(IStockRepository[PackagingStock]):
    @abstractmethod
    async def get_by_packaging(self, packaging_id: int) -> list[PackagingStock]: ...


class IProductStockRepository(IStockRepository[ProductStock]):
    @abstractmethod
    async def get_by_product(self, product_id: int) -> list[ProductStock]: ...

    @abstractmethod
    async def get_last_batch_number(self, year: int) -> int: ...
