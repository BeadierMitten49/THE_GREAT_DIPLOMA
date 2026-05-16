from datetime import date

import pytest

from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.value_objects import OrderStatus
from src.infrastructure.db.repositories.orders import (
    OrderItemRepository,
    OrderRepository,
    ProductReservationRepository,
)

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_next_number = 0


def _order_number() -> int:
    global _next_number
    _next_number += 1
    return _next_number


def make_order(
    customer_id: int = 1,
    delivery_address: str = "ул. Пушкина, 1",
    delivery_date: date = date(2026, 6, 1),
    status: OrderStatus = OrderStatus.created,
    delivery_user_id: int | None = None,
    comment: str | None = None,
    number: int | None = None,
) -> Order:
    return Order(
        customer_id=customer_id,
        delivery_address=delivery_address,
        delivery_date=delivery_date,
        status=status,
        delivery_user_id=delivery_user_id,
        comment=comment,
        number=number if number is not None else _order_number(),
    )


def make_order_item(order_id: int, product_id: int = 1, quantity: int = 10) -> OrderItem:
    return OrderItem(order_id=order_id, product_id=product_id, quantity=quantity)


def make_reservation(order_id: int, stock_id: int = 1, quantity: int = 20) -> ProductReservation:
    return ProductReservation(order_id=order_id, stock_id=stock_id, quantity=quantity)


# ---------------------------------------------------------------------------
# OrderRepository
# ---------------------------------------------------------------------------


class TestOrderRepository:
    async def test_save_and_get_by_id(self, session):
        repo = OrderRepository(session)
        order = make_order(number=100)
        await repo.save(order)

        found = await repo.get_by_id(order.id)
        assert found is not None
        assert found.number == 100
        assert found.customer_id == 1
        assert found.delivery_address == "ул. Пушкина, 1"
        assert found.delivery_date == date(2026, 6, 1)
        assert found.status == OrderStatus.created
        assert found.is_active is True
        assert found.created_at is not None

    async def test_save_returns_id(self, session):
        repo = OrderRepository(session)
        order = make_order()
        id_ = await repo.save(order)
        assert isinstance(id_, int)
        assert id_ == order.id

    async def test_get_by_id_not_found(self, session):
        repo = OrderRepository(session)
        assert await repo.get_by_id(999) is None

    async def test_optional_fields_saved(self, session):
        repo = OrderRepository(session)
        order = make_order(delivery_user_id=5, comment="срочно")
        await repo.save(order)

        found = await repo.get_by_id(order.id)
        assert found.delivery_user_id == 5
        assert found.comment == "срочно"

    async def test_save_updates_status(self, session):
        repo = OrderRepository(session)
        order = make_order()
        await repo.save(order)

        order.change_status(OrderStatus.production)
        await repo.save(order)

        found = await repo.get_by_id(order.id)
        assert found.status == OrderStatus.production

    async def test_save_soft_delete(self, session):
        repo = OrderRepository(session)
        order = make_order()
        await repo.save(order)

        order.delete()
        await repo.save(order)

        found = await repo.get_by_id(order.id)
        assert found.is_active is False

    async def test_get_all_excludes_deleted(self, session):
        repo = OrderRepository(session)
        active = make_order(customer_id=1)
        deleted = make_order(customer_id=2)
        await repo.save(active)
        await repo.save(deleted)
        deleted.delete()
        await repo.save(deleted)

        result = await repo.get_all()
        assert len(result) == 1
        assert result[0].customer_id == 1

    async def test_get_all_includes_deleted_when_flag(self, session):
        repo = OrderRepository(session)
        active = make_order(customer_id=1)
        deleted = make_order(customer_id=2)
        await repo.save(active)
        await repo.save(deleted)
        deleted.delete()
        await repo.save(deleted)

        result = await repo.get_all(include_inactive=True)
        assert len(result) == 2

    async def test_get_by_status(self, session):
        repo = OrderRepository(session)
        await repo.save(make_order(customer_id=1, status=OrderStatus.created))
        await repo.save(make_order(customer_id=2, status=OrderStatus.created))
        await repo.save(make_order(customer_id=3, status=OrderStatus.production))

        result = await repo.get_by_status(OrderStatus.created)
        assert len(result) == 2
        assert all(o.status == OrderStatus.created for o in result)

    async def test_get_by_customer(self, session):
        repo = OrderRepository(session)
        await repo.save(make_order(customer_id=1))
        await repo.save(make_order(customer_id=1))
        await repo.save(make_order(customer_id=2))

        result = await repo.get_by_customer(1)
        assert len(result) == 2
        assert all(o.customer_id == 1 for o in result)

    async def test_get_last_order_number_returns_max(self, session):
        repo = OrderRepository(session)
        await repo.save(make_order(number=1))
        await repo.save(make_order(number=2))
        await repo.save(make_order(number=3))

        assert await repo.get_last_order_number() == 3

    async def test_get_last_order_number_empty_returns_zero(self, session):
        repo = OrderRepository(session)
        assert await repo.get_last_order_number() == 0


# ---------------------------------------------------------------------------
# OrderItemRepository
# ---------------------------------------------------------------------------


class TestOrderItemRepository:
    async def test_save_and_get_by_id(self, session):
        order_repo = OrderRepository(session)
        order = make_order()
        await order_repo.save(order)

        repo = OrderItemRepository(session)
        item = make_order_item(order_id=order.id)
        await repo.save(item)

        found = await repo.get_by_id(item.id)
        assert found is not None
        assert found.order_id == order.id
        assert found.product_id == 1
        assert found.quantity == 10

    async def test_get_by_id_not_found(self, session):
        repo = OrderItemRepository(session)
        assert await repo.get_by_id(999) is None

    async def test_get_by_order(self, session):
        order_repo = OrderRepository(session)
        order = make_order()
        await order_repo.save(order)

        repo = OrderItemRepository(session)
        await repo.save(make_order_item(order_id=order.id, product_id=1))
        await repo.save(make_order_item(order_id=order.id, product_id=2))

        result = await repo.get_by_order(order.id)
        assert len(result) == 2
        assert all(i.order_id == order.id for i in result)

    async def test_get_by_order_empty(self, session):
        repo = OrderItemRepository(session)
        assert await repo.get_by_order(999) == []

    async def test_delete_by_order(self, session):
        order_repo = OrderRepository(session)
        order = make_order()
        await order_repo.save(order)

        repo = OrderItemRepository(session)
        await repo.save(make_order_item(order_id=order.id, product_id=1))
        await repo.save(make_order_item(order_id=order.id, product_id=2))

        await repo.delete_by_order(order.id)
        assert await repo.get_by_order(order.id) == []


# ---------------------------------------------------------------------------
# ProductReservationRepository
# ---------------------------------------------------------------------------


class TestProductReservationRepository:
    async def test_save_and_get_by_id(self, session):
        order_repo = OrderRepository(session)
        order = make_order()
        await order_repo.save(order)

        repo = ProductReservationRepository(session)
        reservation = make_reservation(order_id=order.id)
        await repo.save(reservation)

        found = await repo.get_by_id(reservation.id)
        assert found is not None
        assert found.order_id == order.id
        assert found.stock_id == 1
        assert found.quantity == 20

    async def test_get_by_id_not_found(self, session):
        repo = ProductReservationRepository(session)
        assert await repo.get_by_id(999) is None

    async def test_get_by_order(self, session):
        order_repo = OrderRepository(session)
        order = make_order()
        await order_repo.save(order)

        repo = ProductReservationRepository(session)
        await repo.save(make_reservation(order_id=order.id, stock_id=1))
        await repo.save(make_reservation(order_id=order.id, stock_id=2))

        result = await repo.get_by_order(order.id)
        assert len(result) == 2
        assert all(r.order_id == order.id for r in result)

    async def test_get_by_stock(self, session):
        order_repo = OrderRepository(session)
        o1, o2 = make_order(customer_id=1), make_order(customer_id=2)
        await order_repo.save(o1)
        await order_repo.save(o2)

        repo = ProductReservationRepository(session)
        await repo.save(make_reservation(order_id=o1.id, stock_id=5))
        await repo.save(make_reservation(order_id=o2.id, stock_id=5))
        await repo.save(make_reservation(order_id=o1.id, stock_id=6))

        result = await repo.get_by_stock(5)
        assert len(result) == 2
        assert all(r.stock_id == 5 for r in result)

    async def test_delete_by_order(self, session):
        order_repo = OrderRepository(session)
        order = make_order()
        await order_repo.save(order)

        repo = ProductReservationRepository(session)
        await repo.save(make_reservation(order_id=order.id, stock_id=1))
        await repo.save(make_reservation(order_id=order.id, stock_id=2))

        await repo.delete_by_order(order.id)
        assert await repo.get_by_order(order.id) == []
