from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.orders.value_objects import OrderStatus
from src.domain.tasks.value_objects import TaskStatus


class OrderItemInput(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    customer_id: int
    delivery_address: str
    delivery_date: date
    items: list[OrderItemInput]
    delivery_user_id: int | None = None
    comment: str | None = None


class EditOrderRequest(BaseModel):
    delivery_address: str
    delivery_date: date
    items: list[OrderItemInput]
    delivery_user_id: int | None = None
    comment: str | None = None


class ChangeOrderStatusRequest(BaseModel):
    new_status: OrderStatus


class ReserveProductRequest(BaseModel):
    stock_id: int
    quantity: int = Field(gt=0)


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    product_name: str
    units_per_box: int
    quantity: int


class ProductReservationResponse(BaseModel):
    id: int
    order_id: int
    stock_id: int
    quantity: int


class ItemReservationInfo(BaseModel):
    reservation_id: int
    stock_id: int
    batch_label: str
    quantity: int


class OrderTaskInfo(BaseModel):
    task_id: int
    product_name: str
    quantity: int
    executor_name: str
    deadline: date
    status: TaskStatus


class OrderDrawerResponse(BaseModel):
    order: "OrderResponse"
    items: list[OrderItemResponse]
    reservations_by_item: dict[int, list[ItemReservationInfo]]
    tasks: list[OrderTaskInfo]


class OrderResponse(BaseModel):
    id: int
    number: int
    customer_id: int
    customer_name: str
    delivery_address: str
    delivery_date: date
    status: OrderStatus
    delivery_user_id: int | None
    delivery_user_name: str | None
    comment: str | None
    created_at: datetime | None

