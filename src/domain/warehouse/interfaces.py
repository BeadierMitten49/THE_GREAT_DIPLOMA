from abc import ABC, abstractmethod

from src.domain.warehouse.entities import (
    PackagingStock,
    ProductReservation,
    ProductStock,
    RawMaterialReservation,
    RawMaterialStock,
)


class IRawMaterialStockRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> RawMaterialStock | None: ...

    @abstractmethod
    async def get_all(self) -> list[RawMaterialStock]: ...

    @abstractmethod
    async def get_by_raw_material(self, raw_material_id: int) -> list[RawMaterialStock]: ...

    @abstractmethod
    async def save(self, entity: RawMaterialStock) -> int: ...


class IPackagingStockRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> PackagingStock | None: ...

    @abstractmethod
    async def get_all(self) -> list[PackagingStock]: ...

    @abstractmethod
    async def get_by_packaging(self, packaging_id: int) -> list[PackagingStock]: ...

    @abstractmethod
    async def save(self, entity: PackagingStock) -> int: ...


class IProductStockRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> ProductStock | None: ...

    @abstractmethod
    async def get_all(self) -> list[ProductStock]: ...

    @abstractmethod
    async def get_by_product(self, product_id: int) -> list[ProductStock]: ...

    @abstractmethod
    async def get_last_batch_number(self, year: int) -> int: ...

    @abstractmethod
    async def save(self, entity: ProductStock) -> int: ...


class IRawMaterialReservationRepository(ABC):
    @abstractmethod
    async def save(self, entity: RawMaterialReservation) -> int: ...

    @abstractmethod
    async def get_by_task(self, task_id: int) -> list[RawMaterialReservation]: ...

    @abstractmethod
    async def get_by_stock(self, stock_id: int) -> list[RawMaterialReservation]: ...

    @abstractmethod
    async def release_by_task(self, task_id: int) -> None: ...


class IProductReservationRepository(ABC):
    @abstractmethod
    async def save(self, entity: ProductReservation) -> int: ...

    @abstractmethod
    async def get_by_order(self, order_id: int) -> list[ProductReservation]: ...

    @abstractmethod
    async def get_by_stock(self, stock_id: int) -> list[ProductReservation]: ...

    @abstractmethod
    async def release_by_order(self, order_id: int) -> None: ...
