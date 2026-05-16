from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.application.orders.exceptions import InsufficientStockError, NotFoundError
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.value_objects import OrderStatus
from src.domain.shared.exceptions import InvalidFieldError
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.orders.dependencies import get_order_service


class FakeOrderService:
    def __init__(self) -> None:
        self._orders: dict[int, Order] = {}
        self._items: dict[int, list[OrderItem]] = {}
        self._reservations: dict[int, ProductReservation] = {}
        self._next_order_id = 1
        self._next_reservation_id = 1
        self._next_item_id = 1
        self._next_number = 0

    async def get(self, order_id: int) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Order", order_id)
        return order

    async def get_all(
        self, status: OrderStatus | None = None, customer_id: int | None = None
    ) -> list[Order]:
        orders = [o for o in self._orders.values() if o.is_active]
        if status is not None:
            orders = [o for o in orders if o.status == status]
        if customer_id is not None:
            orders = [o for o in orders if o.customer_id == customer_id]
        return orders

    async def get_items(self, order_id: int) -> list[OrderItem]:
        return self._items.get(order_id, [])

    async def create(
        self,
        customer_id: int,
        delivery_address: str,
        delivery_date: date,
        items: list[tuple[int, int]],
        delivery_user_id: int | None,
        comment: str | None,
    ) -> int:
        self._next_number += 1
        order = Order(
            id=self._next_order_id,
            number=self._next_number,
            customer_id=customer_id,
            delivery_address=delivery_address,
            delivery_date=delivery_date,
            delivery_user_id=delivery_user_id,
            comment=comment,
        )
        self._orders[self._next_order_id] = order
        order_items = []
        for pid, qty in items:
            order_items.append(
                OrderItem(id=self._next_item_id, order_id=self._next_order_id, product_id=pid, quantity=qty)
            )
            self._next_item_id += 1
        self._items[self._next_order_id] = order_items
        self._next_order_id += 1
        return order.id

    async def change_status(self, order_id: int, new_status: OrderStatus) -> None:
        order = self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Order", order_id)
        order.change_status(new_status)

    async def edit(
        self,
        order_id: int,
        delivery_address: str,
        delivery_date: date,
        items: list[tuple[int, int]],
        delivery_user_id: int | None,
        comment: str | None,
    ) -> None:
        order = self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Order", order_id)
        if order.status in (OrderStatus.delivery, OrderStatus.completed):
            raise InvalidFieldError("status", f"cannot edit order in status '{order.status}'")
        order.delivery_address = delivery_address
        order.delivery_date = delivery_date
        order.delivery_user_id = delivery_user_id
        order.comment = comment
        edited_items = []
        for pid, qty in items:
            edited_items.append(
                OrderItem(id=self._next_item_id, order_id=order_id, product_id=pid, quantity=qty)
            )
            self._next_item_id += 1
        self._items[order_id] = edited_items

    async def delete(self, order_id: int) -> None:
        order = self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Order", order_id)
        order.delete()

    async def reserve(self, order_id: int, stock_id: int, quantity: int) -> int:
        if order_id not in self._orders:
            raise NotFoundError("Order", order_id)
        rid = self._next_reservation_id
        self._reservations[rid] = ProductReservation(
            id=rid, order_id=order_id, stock_id=stock_id, quantity=quantity
        )
        self._next_reservation_id += 1
        return rid

    async def release_reservation(self, reservation_id: int) -> None:
        if reservation_id not in self._reservations:
            raise NotFoundError("ProductReservation", reservation_id)
        del self._reservations[reservation_id]

    async def release_all_reservations(self, order_id: int) -> None:
        if order_id not in self._orders:
            raise NotFoundError("Order", order_id)
        self._reservations = {
            rid: r for rid, r in self._reservations.items() if r.order_id != order_id
        }


def _make_director() -> User:
    return User(username="director", full_name="Director", roles=[Role.director], id=1)


@pytest.fixture
def order_svc() -> FakeOrderService:
    return FakeOrderService()


@pytest_asyncio.fixture
async def client(order_svc: FakeOrderService) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: _make_director()
    app.dependency_overrides[get_order_service] = lambda: order_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def saved_order_id(client: AsyncClient) -> int:
    r = await client.post("/api/v1/orders", json={
        "customer_id": 1,
        "delivery_address": "ул. Пушкина, 1",
        "delivery_date": "2026-06-01",
        "items": [{"product_id": 1, "quantity": 100}],
    })
    return r.json()["id"]
