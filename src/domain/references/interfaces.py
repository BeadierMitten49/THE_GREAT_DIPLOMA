from abc import abstractmethod

from src.domain.references.entities import Customer, PackagingCatalog, Product, RawMaterialCatalog
from src.domain.shared.repository import IRepository


class ICustomerRepository(IRepository[Customer]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...


class IProductRepository(IRepository[Product]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...


class IRawMaterialCatalogRepository(IRepository[RawMaterialCatalog]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...


class IPackagingCatalogRepository(IRepository[PackagingCatalog]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...
