from datetime import date, datetime

from pydantic import BaseModel

from src.domain.delivery.value_objects import DeliveryStatus


class CreateDeliveryRequest(BaseModel):
    order_id: int
    executor_id: int
    planned_date: date


class CancelDeliveryRequest(BaseModel):
    reason: str


class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    executor_id: int
    status: DeliveryStatus
    planned_date: date
    started_at: datetime | None
    completed_at: datetime | None
    cancellation_reason: str | None
