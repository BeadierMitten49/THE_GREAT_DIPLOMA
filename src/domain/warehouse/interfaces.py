from abc import abstractmethod

from src.domain.shared.repository import IPlainRepository
from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock


class IRawMaterialStockRepository(IPlainRepository[RawMaterialStock]):
    @abstractmethod
    async def get_by_raw_material(self, raw_material_id: int) -> list[RawMaterialStock]: ...

    @abstractmethod
    async def delete(self, id: int) -> None: ...


class IPackagingStockRepository(IPlainRepository[PackagingStock]):
    @abstractmethod
    async def get_by_packaging(self, packaging_id: int) -> list[PackagingStock]: ...

    @abstractmethod
    async def delete(self, id: int) -> None: ...


class IProductStockRepository(IPlainRepository[ProductStock]):
    @abstractmethod
    async def get_by_product(self, product_id: int) -> list[ProductStock]: ...

    @abstractmethod
    async def get_last_batch_number(self, year: int) -> int: ...

    @abstractmethod
    async def delete(self, id: int) -> None: ...
