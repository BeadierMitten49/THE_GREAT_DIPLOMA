from datetime import date

import pytest

from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.interfaces import (
    IOrderItemRepository,
    IOrderRepository,
    IProductReservationRepository,
)
from src.domain.orders.value_objects import OrderStatus
from src.domain.warehouse.entities import ProductStock
from src.domain.warehouse.interfaces import IProductStockRepository


class FakeOrderRepository(IOrderRepository):
    def __init__(self) -> None:
        self._store: dict[int, Order] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> Order | None:
        return self._store.get(id)

    async def get_all(self, include_inactive: bool = False) -> list[Order]:
        return [o for o in self._store.values() if include_inactive or o.is_active]

    async def save(self, entity: Order) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_by_status(self, status: OrderStatus) -> list[Order]:
        return [o for o in self._store.values() if o.status == status]

    async def get_by_customer(self, customer_id: int) -> list[Order]:
        return [o for o in self._store.values() if o.customer_id == customer_id]

    async def get_last_order_number(self) -> int:
        numbers = [o.number for o in self._store.values() if o.number is not None]
        return max(numbers) if numbers else 0


class FakeOrderItemRepository(IOrderItemRepository):
    def __init__(self) -> None:
        self._store: dict[int, OrderItem] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> OrderItem | None:
        return self._store.get(id)

    async def get_all(self) -> list[OrderItem]:
        return list(self._store.values())

    async def save(self, entity: OrderItem) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_by_order(self, order_id: int) -> list[OrderItem]:
        return [i for i in self._store.values() if i.order_id == order_id]

    async def delete_by_order(self, order_id: int) -> None:
        to_delete = [k for k, v in self._store.items() if v.order_id == order_id]
        for k in to_delete:
            del self._store[k]


class FakeProductReservationRepository(IProductReservationRepository):
    def __init__(self) -> None:
        self._store: dict[int, ProductReservation] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> ProductReservation | None:
        return self._store.get(id)

    async def get_all(self) -> list[ProductReservation]:
        return list(self._store.values())

    async def save(self, entity: ProductReservation) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_by_order(self, order_id: int) -> list[ProductReservation]:
        return [r for r in self._store.values() if r.order_id == order_id]

    async def get_by_stock(self, stock_id: int) -> list[ProductReservation]:
        return [r for r in self._store.values() if r.stock_id == stock_id]

    async def delete_by_order(self, order_id: int) -> None:
        to_delete = [k for k, v in self._store.items() if v.order_id == order_id]
        for k in to_delete:
            del self._store[k]

    async def delete_by_id(self, reservation_id: int) -> None:
        self._store.pop(reservation_id, None)


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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def order_repo() -> FakeOrderRepository:
    return FakeOrderRepository()


@pytest.fixture
def item_repo() -> FakeOrderItemRepository:
    return FakeOrderItemRepository()


@pytest.fixture
def reservation_repo() -> FakeProductReservationRepository:
    return FakeProductReservationRepository()


@pytest.fixture
def stock_repo() -> FakeProductStockRepository:
    return FakeProductStockRepository()


@pytest.fixture
async def saved_order(order_repo) -> Order:
    order = Order(
        customer_id=1,
        delivery_address="ул. Пушкина, 1",
        delivery_date=date(2026, 6, 1),
        number=1,
    )
    await order_repo.save(order)
    return order


@pytest.fixture
async def saved_stock(stock_repo) -> ProductStock:
    stock = ProductStock(
        product_id=1,
        quantity=200,
        batch_number=1,
        batch_year=2026,
        arrival_date=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
    )
    await stock_repo.save(stock)
    return stock
