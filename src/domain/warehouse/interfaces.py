from abc import abstractmethod

from src.domain.shared.repository import IPlainRepository
from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock


class IRawMaterialStockRepository(IPlainRepository[RawMaterialStock]):
    @abstractmethod
    async def get_by_raw_material(self, raw_material_id: int) -> list[RawMaterialStock]: ...


class IPackagingStockRepository(IPlainRepository[PackagingStock]):
    @abstractmethod
    async def get_by_packaging(self, packaging_id: int) -> list[PackagingStock]: ...


class IProductStockRepository(IPlainRepository[ProductStock]):
    @abstractmethod
    async def get_by_product(self, product_id: int) -> list[ProductStock]: ...

    @abstractmethod
    async def get_last_batch_number(self, year: int) -> int: ...
