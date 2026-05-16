from abc import abstractmethod

from src.domain.references.entities import Customer, PackagingCatalog, Product, RawMaterialCatalog
from src.domain.shared.repository import ISoftDeleteRepository


class ICustomerRepository(ISoftDeleteRepository[Customer]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...


class IProductRepository(ISoftDeleteRepository[Product]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...


class IRawMaterialCatalogRepository(ISoftDeleteRepository[RawMaterialCatalog]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...


class IPackagingCatalogRepository(ISoftDeleteRepository[PackagingCatalog]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...
