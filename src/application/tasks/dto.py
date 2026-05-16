from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from src.domain.tasks.value_objects import TaskType


@dataclass(frozen=True)
class CreateTaskDTO:
    product_id: int
    quantity: int
    executor_id: int
    start_date: date
    deadline: date
    task_type: TaskType
    order_id: int | None = None
    comment: str | None = None


@dataclass(frozen=True)
class ConsumptionInputDTO:
    raw_material_id: int
    actual_qty: Decimal
    waste_qty: Decimal | None = None


@dataclass(frozen=True)
class CompleteTaskDTO:
    task_id: int
    actual_quantity: int
    consumptions: list[ConsumptionInputDTO] = field(default_factory=list)
    comment: str | None = None
