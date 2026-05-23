from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.application.shared.exceptions import NotFoundError as SharedNotFoundError
from src.application.warehouse.exceptions import NotFoundError
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock
from src.domain.shared.exceptions import InvalidFieldError
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.warehouse.dependencies import (
    get_packaging_stock_service,
    get_product_stock_service,
    get_raw_material_stock_service,
)


# ---------------------------------------------------------------------------
# Fake services
# ---------------------------------------------------------------------------


class FakeRawMaterialStockService:
    def __init__(self) -> None:
        self._store: dict[int, RawMaterialStock] = {}
        self._next_id = 1

    async def get(self, id: int) -> RawMaterialStock:
        item = self._store.get(id)
        if item is None:
            raise NotFoundError("RawMaterialStock", id)
        return item

    async def get_all(self) -> list[RawMaterialStock]:
        return list(self._store.values())

    async def get_by_material(self, raw_material_id: int) -> list[RawMaterialStock]:
        return [s for s in self._store.values() if s.raw_material_id == raw_material_id]

    async def get_reserved(self, stock_id: int) -> Decimal:
        return Decimal("0")

    async def arrival(
        self,
        raw_material_id: int,
        quantity: Decimal,
        arrival_date: date,
        expiry_date: date,
        comment: str | None,
    ) -> int:
        stock = RawMaterialStock(
            id=self._next_id,
            raw_material_id=raw_material_id,
            quantity=quantity,
            arrival_date=arrival_date,
            expiry_date=expiry_date,
            comment=comment,
        )
        self._store[self._next_id] = stock
        self._next_id += 1
        return stock.id

    async def write_off(self, stock_id: int, amount: Decimal) -> None:
        stock = self._store.get(stock_id)
        if stock is None:
            raise NotFoundError("RawMaterialStock", stock_id)
        stock.write_off(amount)

    async def adjust(self, stock_id: int, quantity: Decimal, comment: str | None) -> None:
        stock = self._store.get(stock_id)
        if stock is None:
            raise NotFoundError("RawMaterialStock", stock_id)
        stock.adjust(quantity, comment)


class FakePackagingStockService:
    def __init__(self) -> None:
        self._store: dict[int, PackagingStock] = {}
        self._next_id = 1

    async def get(self, id: int) -> PackagingStock:
        item = self._store.get(id)
        if item is None:
            raise NotFoundError("PackagingStock", id)
        return item

    async def get_all(self) -> list[PackagingStock]:
        return list(self._store.values())

    async def get_by_packaging(self, packaging_id: int) -> list[PackagingStock]:
        return [s for s in self._store.values() if s.packaging_id == packaging_id]

    async def arrival(self, packaging_id: int, quantity: int, comment: str | None) -> int:
        stock = PackagingStock(
            id=self._next_id,
            packaging_id=packaging_id,
            quantity=quantity,
            comment=comment,
        )
        self._store[self._next_id] = stock
        self._next_id += 1
        return stock.id

    async def write_off(self, stock_id: int, amount: int) -> None:
        stock = self._store.get(stock_id)
        if stock is None:
            raise NotFoundError("PackagingStock", stock_id)
        stock.write_off(amount)


class FakeProductStockService:
    def __init__(self) -> None:
        self._store: dict[int, ProductStock] = {}
        self._next_id = 1

    async def get(self, id: int) -> ProductStock:
        item = self._store.get(id)
        if item is None:
            raise NotFoundError("ProductStock", id)
        return item

    async def get_all(self) -> list[ProductStock]:
        return list(self._store.values())

    async def get_by_product(self, product_id: int) -> list[ProductStock]:
        return [s for s in self._store.values() if s.product_id == product_id]

    async def get_reserved(self, stock_id: int) -> tuple[int, list[int]]:
        return 0, []

    async def arrival(
        self,
        product_id: int,
        quantity: int,
        arrival_date: date,
        expiry_date: date,
        comment: str | None,
    ) -> int:
        stock = ProductStock(
            id=self._next_id,
            product_id=product_id,
            quantity=quantity,
            batch_number=1,
            batch_year=arrival_date.year,
            arrival_date=arrival_date,
            expiry_date=expiry_date,
            comment=comment,
        )
        self._store[self._next_id] = stock
        self._next_id += 1
        return stock.id

    async def get_pending_acceptances(self) -> list[dict]:
        return [
            {
                "task_id": 1,
                "product_id": 1,
                "product_name": "Молоко 3,2% 1 л",
                "planned_quantity": 100,
                "actual_quantity": 95,
                "completed_at": "2026-05-20T12:00:00",
            },
        ]

    async def accept_from_task(self, task_id: int) -> int:
        if task_id == 999:
            raise SharedNotFoundError("ProductionTask", task_id)
        return await self.arrival(1, 100, date.today(), date.today(), f"Task #{task_id}")

    async def adjust(self, stock_id: int, quantity: int, comment: str | None) -> None:
        stock = self._store.get(stock_id)
        if stock is None:
            raise NotFoundError("ProductStock", stock_id)
        stock.adjust(quantity, comment)

    async def write_off(self, stock_id: int, amount: int) -> None:
        stock = self._store.get(stock_id)
        if stock is None:
            raise NotFoundError("ProductStock", stock_id)
        stock.write_off(amount)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def raw_material_stock_svc() -> FakeRawMaterialStockService:
    return FakeRawMaterialStockService()


@pytest.fixture
def packaging_stock_svc() -> FakePackagingStockService:
    return FakePackagingStockService()


@pytest.fixture
def product_stock_svc() -> FakeProductStockService:
    return FakeProductStockService()


def _make_director() -> User:
    return User(username="director", full_name="Director", roles=[Role.director], id=1)


@pytest_asyncio.fixture
async def client(
    raw_material_stock_svc, packaging_stock_svc, product_stock_svc
) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: _make_director()
    app.dependency_overrides[get_raw_material_stock_service] = lambda: raw_material_stock_svc
    app.dependency_overrides[get_packaging_stock_service] = lambda: packaging_stock_svc
    app.dependency_overrides[get_product_stock_service] = lambda: product_stock_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
