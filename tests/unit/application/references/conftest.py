from decimal import Decimal

import pytest

from src.domain.references.entities import (
    Customer,
    PackagingCatalog,
    Product,
    RawMaterialCatalog,
)
from src.domain.references.interfaces import (
    ICustomerRepository,
    IPackagingCatalogRepository,
    IProductRepository,
    IRawMaterialCatalogRepository,
)


class FakeRepository[TEntity]:
    def __init__(self) -> None:
        self._store: dict[int, TEntity] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> TEntity | None:
        return self._store.get(id)

    async def get_all(self, include_inactive: bool = False) -> list[TEntity]:
        items = list(self._store.values())
        if not include_inactive:
            items = [i for i in items if i.is_active]
        return items

    async def save(self, entity: TEntity) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        return any(
            i.name == name and i.id != exclude_id
            for i in self._store.values()
        )


class FakeCustomerRepository(FakeRepository[Customer], ICustomerRepository):
    pass


class FakeProductRepository(FakeRepository[Product], IProductRepository):
    pass


class FakeRawMaterialRepository(FakeRepository[RawMaterialCatalog], IRawMaterialCatalogRepository):
    pass


class FakePackagingRepository(FakeRepository[PackagingCatalog], IPackagingCatalogRepository):
    pass


@pytest.fixture
def customer_repo() -> FakeCustomerRepository:
    return FakeCustomerRepository()


@pytest.fixture
def product_repo() -> FakeProductRepository:
    return FakeProductRepository()


@pytest.fixture
def raw_material_repo() -> FakeRawMaterialRepository:
    return FakeRawMaterialRepository()


@pytest.fixture
def packaging_repo() -> FakePackagingRepository:
    return FakePackagingRepository()


# --- prefilled fixtures ---

@pytest.fixture
async def saved_customer(customer_repo) -> Customer:
    customer = Customer(name="ООО Ромашка", default_address="ул. Ленина, 1")
    await customer_repo.save(customer)
    return customer


@pytest.fixture
async def saved_product(product_repo) -> Product:
    product = Product(name="Сахар фасованный", units_per_box=12, shelf_life_days=365, critical_stock=100)
    await product_repo.save(product)
    return product


@pytest.fixture
async def saved_raw_material(raw_material_repo) -> RawMaterialCatalog:
    item = RawMaterialCatalog(name="Сахар-сырец", unit="кг", shelf_life_days=730, critical_stock=Decimal("50"))
    await raw_material_repo.save(item)
    return item


@pytest.fixture
async def saved_packaging(packaging_repo) -> PackagingCatalog:
    item = PackagingCatalog(name="Пакет 1кг", unit="шт", critical_stock=500)
    await packaging_repo.save(item)
    return item
