from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.application.references.exceptions import AlreadyExistsError, NotFoundError
from src.domain.references.entities import (
    Customer,
    PackagingCatalog,
    Product,
    RawMaterialCatalog,
    RecipeLine,
)
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.references.dependencies import (
    get_customer_service,
    get_packaging_service,
    get_product_service,
    get_raw_material_service,
)


# ---------------------------------------------------------------------------
# Fake services
# ---------------------------------------------------------------------------


class FakeCustomerService:
    def __init__(self) -> None:
        self._store: dict[int, Customer] = {}
        self._next_id = 1

    async def get(self, id: int) -> Customer:
        item = self._store.get(id)
        if item is None:
            raise NotFoundError("Customer", id)
        return item

    async def get_all(self, include_inactive: bool = False) -> list[Customer]:
        items = list(self._store.values())
        return items if include_inactive else [i for i in items if i.is_active]

    async def create(self, name: str, default_address: str, contact: str = "", comment: str = "") -> int:
        if any(c.name == name for c in self._store.values()):
            raise AlreadyExistsError("\1", "name", name)
        item = Customer(name=name, default_address=default_address, contact=contact, comment=comment, id=self._next_id)
        self._store[self._next_id] = item
        self._next_id += 1
        return item.id

    async def update(self, id: int, name: str, default_address: str, contact: str = "", comment: str = "") -> None:
        item = await self.get(id)
        if any(c.name == name and c.id != id for c in self._store.values()):
            raise AlreadyExistsError("\1", "name", name)
        item.name = name
        item.default_address = default_address
        item.contact = contact
        item.comment = comment

    async def deactivate(self, id: int) -> None:
        (await self.get(id)).is_active = False

    async def activate(self, id: int) -> None:
        (await self.get(id)).is_active = True


class FakeProductService:
    def __init__(self) -> None:
        self._store: dict[int, Product] = {}
        self._next_id = 1

    async def get(self, id: int) -> Product:
        item = self._store.get(id)
        if item is None:
            raise NotFoundError("Product", id)
        return item

    async def get_all(self, include_inactive: bool = False) -> list[Product]:
        items = list(self._store.values())
        return items if include_inactive else [i for i in items if i.is_active]

    async def create(
        self, name: str, units_per_box: int, shelf_life_days: int, critical_stock: int
    ) -> int:
        if any(p.name == name for p in self._store.values()):
            raise AlreadyExistsError("\1", "name", name)
        item = Product(
            name=name,
            units_per_box=units_per_box,
            shelf_life_days=shelf_life_days,
            critical_stock=critical_stock,
            id=self._next_id,
        )
        self._store[self._next_id] = item
        self._next_id += 1
        return item.id

    async def update(
        self, id: int, name: str, units_per_box: int, shelf_life_days: int, critical_stock: int
    ) -> None:
        item = await self.get(id)
        if any(p.name == name and p.id != id for p in self._store.values()):
            raise AlreadyExistsError("\1", "name", name)
        item.name = name
        item.units_per_box = units_per_box
        item.shelf_life_days = shelf_life_days
        item.critical_stock = critical_stock

    async def set_recipe(self, id: int, lines: list[tuple[int, Decimal, Decimal]]) -> None:
        item = await self.get(id)
        item.recipe = [
            RecipeLine(raw_material_id=rm_id, consumption_per_unit=c, waste_percentage=w, id=i + 1)
            for i, (rm_id, c, w) in enumerate(lines)
        ]

    async def deactivate(self, id: int) -> None:
        (await self.get(id)).is_active = False

    async def activate(self, id: int) -> None:
        (await self.get(id)).is_active = True


class FakeRawMaterialService:
    def __init__(self) -> None:
        self._store: dict[int, RawMaterialCatalog] = {}
        self._next_id = 1

    async def get(self, id: int) -> RawMaterialCatalog:
        item = self._store.get(id)
        if item is None:
            raise NotFoundError("RawMaterialCatalog", id)
        return item

    async def get_all(self, include_inactive: bool = False) -> list[RawMaterialCatalog]:
        items = list(self._store.values())
        return items if include_inactive else [i for i in items if i.is_active]

    async def create(
        self, name: str, unit: str, shelf_life_days: int, critical_stock: Decimal, comment: str = ""
    ) -> int:
        if any(r.name == name for r in self._store.values()):
            raise AlreadyExistsError("\1", "name", name)
        item = RawMaterialCatalog(
            name=name,
            unit=unit,
            shelf_life_days=shelf_life_days,
            critical_stock=critical_stock,
            comment=comment,
            id=self._next_id,
        )
        self._store[self._next_id] = item
        self._next_id += 1
        return item.id

    async def update(
        self, id: int, name: str, unit: str, shelf_life_days: int, critical_stock: Decimal, comment: str = ""
    ) -> None:
        item = await self.get(id)
        if any(r.name == name and r.id != id for r in self._store.values()):
            raise AlreadyExistsError("\1", "name", name)
        item.name = name
        item.unit = unit
        item.shelf_life_days = shelf_life_days
        item.critical_stock = critical_stock
        item.comment = comment

    async def deactivate(self, id: int) -> None:
        (await self.get(id)).is_active = False

    async def activate(self, id: int) -> None:
        (await self.get(id)).is_active = True


class FakePackagingService:
    def __init__(self) -> None:
        self._store: dict[int, PackagingCatalog] = {}
        self._next_id = 1

    async def get(self, id: int) -> PackagingCatalog:
        item = self._store.get(id)
        if item is None:
            raise NotFoundError("PackagingCatalog", id)
        return item

    async def get_all(self, include_inactive: bool = False) -> list[PackagingCatalog]:
        items = list(self._store.values())
        return items if include_inactive else [i for i in items if i.is_active]

    async def create(self, name: str, unit: str, critical_stock: int, comment: str = "") -> int:
        if any(p.name == name for p in self._store.values()):
            raise AlreadyExistsError("\1", "name", name)
        item = PackagingCatalog(
            name=name, unit=unit, critical_stock=critical_stock, comment=comment, id=self._next_id
        )
        self._store[self._next_id] = item
        self._next_id += 1
        return item.id

    async def update(self, id: int, name: str, unit: str, critical_stock: int, comment: str = "") -> None:
        item = await self.get(id)
        if any(p.name == name and p.id != id for p in self._store.values()):
            raise AlreadyExistsError("\1", "name", name)
        item.name = name
        item.unit = unit
        item.critical_stock = critical_stock
        item.comment = comment

    async def deactivate(self, id: int) -> None:
        (await self.get(id)).is_active = False

    async def activate(self, id: int) -> None:
        (await self.get(id)).is_active = True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def customer_svc() -> FakeCustomerService:
    return FakeCustomerService()


@pytest.fixture
def product_svc() -> FakeProductService:
    return FakeProductService()


@pytest.fixture
def raw_material_svc() -> FakeRawMaterialService:
    return FakeRawMaterialService()


@pytest.fixture
def packaging_svc() -> FakePackagingService:
    return FakePackagingService()


def _make_director() -> User:
    return User(username="director", full_name="Director", roles=[Role.director], id=1)


@pytest_asyncio.fixture
async def client(customer_svc, product_svc, raw_material_svc, packaging_svc) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: _make_director()
    app.dependency_overrides[get_customer_service] = lambda: customer_svc
    app.dependency_overrides[get_product_service] = lambda: product_svc
    app.dependency_overrides[get_raw_material_service] = lambda: raw_material_svc
    app.dependency_overrides[get_packaging_service] = lambda: packaging_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
