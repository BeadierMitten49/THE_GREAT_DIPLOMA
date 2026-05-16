from datetime import date
from decimal import Decimal

import pytest

from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock
from src.domain.warehouse.interfaces import (
    IPackagingStockRepository,
    IProductStockRepository,
    IRawMaterialStockRepository,
)


class FakeRawMaterialStockRepository(IRawMaterialStockRepository):
    def __init__(self) -> None:
        self._store: dict[int, RawMaterialStock] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> RawMaterialStock | None:
        return self._store.get(id)

    async def get_all(self) -> list[RawMaterialStock]:
        return list(self._store.values())

    async def save(self, entity: RawMaterialStock) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_by_raw_material(self, raw_material_id: int) -> list[RawMaterialStock]:
        return [s for s in self._store.values() if s.raw_material_id == raw_material_id]


class FakePackagingStockRepository(IPackagingStockRepository):
    def __init__(self) -> None:
        self._store: dict[int, PackagingStock] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> PackagingStock | None:
        return self._store.get(id)

    async def get_all(self) -> list[PackagingStock]:
        return list(self._store.values())

    async def save(self, entity: PackagingStock) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_by_packaging(self, packaging_id: int) -> list[PackagingStock]:
        return [s for s in self._store.values() if s.packaging_id == packaging_id]


class FakeProductStockRepository(IProductStockRepository):
    def __init__(self) -> None:
        self._store: dict[int, ProductStock] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> ProductStock | None:
        return self._store.get(id)

    async def get_all(self) -> list[ProductStock]:
        return list(self._store.values())

    async def save(self, entity: ProductStock) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_by_product(self, product_id: int) -> list[ProductStock]:
        return [s for s in self._store.values() if s.product_id == product_id]

    async def get_last_batch_number(self, year: int) -> int:
        numbers = [s.batch_number for s in self._store.values() if s.batch_year == year]
        return max(numbers) if numbers else 0


@pytest.fixture
def raw_material_stock_repo() -> FakeRawMaterialStockRepository:
    return FakeRawMaterialStockRepository()


@pytest.fixture
def packaging_stock_repo() -> FakePackagingStockRepository:
    return FakePackagingStockRepository()


@pytest.fixture
def product_stock_repo() -> FakeProductStockRepository:
    return FakeProductStockRepository()


# --- prefilled fixtures ---

@pytest.fixture
async def saved_raw_material_stock(raw_material_stock_repo) -> RawMaterialStock:
    stock = RawMaterialStock(
        raw_material_id=1,
        quantity=Decimal("100.0"),
        arrival_date=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
    )
    await raw_material_stock_repo.save(stock)
    return stock


@pytest.fixture
async def saved_packaging_stock(packaging_stock_repo) -> PackagingStock:
    stock = PackagingStock(packaging_id=1, quantity=500)
    await packaging_stock_repo.save(stock)
    return stock


@pytest.fixture
async def saved_product_stock(product_stock_repo) -> ProductStock:
    stock = ProductStock(
        product_id=1,
        quantity=100,
        batch_number=1,
        batch_year=2026,
        arrival_date=date(2026, 1, 1),
        expiry_date=date(2026, 6, 30),
    )
    await product_stock_repo.save(stock)
    return stock
