from dataclasses import dataclass
from datetime import date, datetime

from src.domain.orders.value_objects import OrderStatus
from src.domain.shared.exceptions import InvalidFieldError

_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.created: {OrderStatus.production, OrderStatus.assembly},
    OrderStatus.production: {OrderStatus.assembly},
    OrderStatus.assembly: {OrderStatus.delivery},
    OrderStatus.delivery: {OrderStatus.completed},
    OrderStatus.completed: set(),
}


@dataclass
class Order:
    customer_id: int
    delivery_address: str
    delivery_date: date
    status: OrderStatus = OrderStatus.created
    id: int | None = None
    number: int | None = None
    delivery_user_id: int | None = None
    comment: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    def change_status(self, new_status: OrderStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS[self.status]
        if new_status not in allowed:
            raise InvalidFieldError(
                "status",
                f"transition from '{self.status}' to '{new_status}' is not allowed",
            )
        self.status = new_status

    def delete(self) -> None:
        if not self.is_active:
            raise InvalidFieldError("is_active", "order is already deleted")
        if self.status in (OrderStatus.delivery, OrderStatus.completed):
            raise InvalidFieldError(
                "status",
                f"cannot delete order in status '{self.status}'",
            )
        self.is_active = False


@dataclass
class OrderItem:
    order_id: int
    product_id: int
    quantity: int
    id: int | None = None


@dataclass
class ProductReservation:
    order_id: int
    stock_id: int
    quantity: int
    id: int | None = None
