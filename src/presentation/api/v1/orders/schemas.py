from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.orders.value_objects import OrderStatus


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
    quantity: int


class OrderResponse(BaseModel):
    id: int
    number: int
    customer_id: int
    delivery_address: str
    delivery_date: date
    status: OrderStatus
    delivery_user_id: int | None
    comment: str | None
    created_at: datetime | None

