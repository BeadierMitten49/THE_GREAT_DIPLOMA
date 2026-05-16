from datetime import date

import pytest

from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.value_objects import OrderStatus
from src.domain.shared.exceptions import InvalidFieldError

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# OrderStatus
# ---------------------------------------------------------------------------


class TestOrderStatus:
    def test_all_values(self):
        assert OrderStatus.created == "created"
        assert OrderStatus.production == "production"
        assert OrderStatus.assembly == "assembly"
        assert OrderStatus.delivery == "delivery"
        assert OrderStatus.completed == "completed"


# ---------------------------------------------------------------------------
# Order.change_status — valid transitions
# ---------------------------------------------------------------------------


class TestOrderChangeStatusValid:
    def _make(self, status: OrderStatus = OrderStatus.created) -> Order:
        return Order(
            customer_id=1,
            delivery_address="ул. Пушкина, 1",
            delivery_date=date(2026, 6, 1),
            status=status,
            number=1,
        )

    def test_created_to_production(self):
        order = self._make(OrderStatus.created)
        order.change_status(OrderStatus.production)
        assert order.status == OrderStatus.production

    def test_created_to_assembly(self):
        order = self._make(OrderStatus.created)
        order.change_status(OrderStatus.assembly)
        assert order.status == OrderStatus.assembly

    def test_production_to_assembly(self):
        order = self._make(OrderStatus.production)
        order.change_status(OrderStatus.assembly)
        assert order.status == OrderStatus.assembly

    def test_assembly_to_delivery(self):
        order = self._make(OrderStatus.assembly)
        order.change_status(OrderStatus.delivery)
        assert order.status == OrderStatus.delivery

    def test_delivery_to_completed(self):
        order = self._make(OrderStatus.delivery)
        order.change_status(OrderStatus.completed)
        assert order.status == OrderStatus.completed


# ---------------------------------------------------------------------------
# Order.change_status — invalid transitions
# ---------------------------------------------------------------------------


class TestOrderChangeStatusInvalid:
    def _make(self, status: OrderStatus) -> Order:
        return Order(
            customer_id=1,
            delivery_address="ул. Пушкина, 1",
            delivery_date=date(2026, 6, 1),
            status=status,
            number=1,
        )

    def test_created_to_delivery_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.created).change_status(OrderStatus.delivery)

    def test_created_to_completed_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.created).change_status(OrderStatus.completed)

    def test_production_to_delivery_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.production).change_status(OrderStatus.delivery)

    def test_production_to_completed_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.production).change_status(OrderStatus.completed)

    def test_assembly_to_production_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.assembly).change_status(OrderStatus.production)

    def test_assembly_to_completed_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.assembly).change_status(OrderStatus.completed)

    def test_delivery_to_production_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.delivery).change_status(OrderStatus.production)

    def test_delivery_to_assembly_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.delivery).change_status(OrderStatus.assembly)

    def test_completed_to_any_raises(self):
        for status in OrderStatus:
            with pytest.raises(InvalidFieldError):
                self._make(OrderStatus.completed).change_status(status)

    def test_same_status_raises(self):
        with pytest.raises(InvalidFieldError):
            self._make(OrderStatus.created).change_status(OrderStatus.created)


# ---------------------------------------------------------------------------
# Order.delete
# ---------------------------------------------------------------------------


class TestOrderDelete:
    def _make(self, status: OrderStatus = OrderStatus.created) -> Order:
        return Order(
            customer_id=1,
            delivery_address="ул. Пушкина, 1",
            delivery_date=date(2026, 6, 1),
            status=status,
        )

    def test_delete_sets_is_active_false(self):
        order = self._make()
        order.delete()
        assert order.is_active is False

    def test_delete_production_is_allowed(self):
        order = self._make(OrderStatus.production)
        order.delete()
        assert order.is_active is False

    def test_delete_assembly_is_allowed(self):
        order = self._make(OrderStatus.assembly)
        order.delete()
        assert order.is_active is False

    def test_delete_delivery_raises(self):
        order = self._make(OrderStatus.delivery)
        with pytest.raises(InvalidFieldError):
            order.delete()

    def test_delete_completed_raises(self):
        order = self._make(OrderStatus.completed)
        with pytest.raises(InvalidFieldError):
            order.delete()

    def test_double_delete_raises(self):
        order = self._make()
        order.delete()
        with pytest.raises(InvalidFieldError):
            order.delete()


# ---------------------------------------------------------------------------
# OrderItem
# ---------------------------------------------------------------------------


class TestOrderItem:
    def test_creation(self):
        item = OrderItem(order_id=1, product_id=2, quantity=10)
        assert item.order_id == 1
        assert item.product_id == 2
        assert item.quantity == 10
        assert item.id is None

    def test_id_is_optional(self):
        item = OrderItem(order_id=1, product_id=2, quantity=10, id=5)
        assert item.id == 5


# ---------------------------------------------------------------------------
# ProductReservation
# ---------------------------------------------------------------------------


class TestProductReservation:
    def test_creation(self):
        reservation = ProductReservation(order_id=1, stock_id=3, quantity=20)
        assert reservation.order_id == 1
        assert reservation.stock_id == 3
        assert reservation.quantity == 20
        assert reservation.id is None

    def test_id_is_optional(self):
        reservation = ProductReservation(order_id=1, stock_id=3, quantity=20, id=7)
        assert reservation.id == 7
