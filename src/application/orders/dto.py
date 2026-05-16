from dataclasses import dataclass
from datetime import date

from src.domain.orders.value_objects import OrderStatus


@dataclass(frozen=True)
class CreateOrderDTO:
    customer_id: int
    delivery_address: str
    delivery_date: date
    items: list[tuple[int, int]]  # (product_id, quantity)
    delivery_user_id: int | None = None
    comment: str | None = None


@dataclass(frozen=True)
class EditOrderDTO:
    order_id: int
    delivery_address: str
    delivery_date: date
    items: list[tuple[int, int]]  # (product_id, quantity)
    delivery_user_id: int | None = None
    comment: str | None = None


@dataclass(frozen=True)
class ChangeOrderStatusDTO:
    order_id: int
    new_status: OrderStatus
