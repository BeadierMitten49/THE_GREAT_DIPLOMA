from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from src.domain.tasks.value_objects import TaskStatus, TaskType


class ConsumptionInput(BaseModel):
    raw_material_id: int
    actual_qty: Decimal
    waste_qty: Decimal | None = None


class CreateTaskRequest(BaseModel):
    product_id: int
    quantity: int
    executor_id: int
    start_date: date
    deadline: date
    task_type: TaskType
    order_id: int | None = None
    comment: str | None = None


class StopTaskRequest(BaseModel):
    reason: str


class CompleteTaskRequest(BaseModel):
    actual_quantity: int
    consumptions: list[ConsumptionInput] = []
    comment: str | None = None


class ReassignTaskRequest(BaseModel):
    executor_id: int


class TaskResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    executor_id: int
    start_date: date
    deadline: date
    task_type: TaskType
    status: TaskStatus
    order_id: int | None
    comment: str | None
    created_at: datetime | None
    actual_start_at: datetime | None
    actual_end_at: datetime | None


class CreateTaskResponse(BaseModel):
    id: int
    insufficient_materials: list[int]


class TaskStopInfo(BaseModel):
    id: int
    reason: str
    stopped_at: datetime
    resumed_at: datetime | None


class TaskCompletionConsumptionInfo(BaseModel):
    raw_material_id: int
    raw_material_name: str
    planned_qty: Decimal
    actual_qty: Decimal
    waste_qty: Decimal | None


class TaskCompletionInfo(BaseModel):
    actual_quantity: int
    comment: str | None
    consumptions: list[TaskCompletionConsumptionInfo]


class RawMaterialReservationInfo(BaseModel):
    id: int
    stock_id: int
    raw_material_name: str
    quantity: Decimal
    batch_label: str


class TaskDrawerResponse(BaseModel):
    task: TaskResponse
    product_name: str
    executor_name: str
    stops: list[TaskStopInfo]
    completion: TaskCompletionInfo | None
    reservations: list[RawMaterialReservationInfo]
