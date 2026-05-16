from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Protocol

from src.domain.shared.exceptions import InvalidFieldError
from src.domain.tasks.value_objects import TaskStatus, TaskType


@dataclass
class ProductionTask:
    product_id: int
    quantity: int
    executor_id: int
    start_date: date
    deadline: date
    task_type: TaskType
    status: TaskStatus = TaskStatus.created
    id: int | None = None
    order_id: int | None = None
    comment: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None

    def start(self) -> None:
        if self.status != TaskStatus.created:
            raise InvalidFieldError("status", f"cannot start task in status '{self.status}'")
        self.status = TaskStatus.in_progress
        self.actual_start_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        if self.status != TaskStatus.in_progress:
            raise InvalidFieldError("status", f"cannot stop task in status '{self.status}'")
        self.status = TaskStatus.stopped

    def resume(self) -> None:
        if self.status != TaskStatus.stopped:
            raise InvalidFieldError("status", f"cannot resume task in status '{self.status}'")
        self.status = TaskStatus.in_progress

    def complete(self) -> None:
        if self.status != TaskStatus.in_progress:
            raise InvalidFieldError("status", f"cannot complete task in status '{self.status}'")
        self.status = TaskStatus.completed
        self.actual_end_at = datetime.now(timezone.utc)

    def close(self) -> None:
        if self.status != TaskStatus.completed:
            raise InvalidFieldError("status", f"cannot close task in status '{self.status}'")
        self.status = TaskStatus.closed

    def delete(self) -> None:
        if not self.is_active:
            raise InvalidFieldError("is_active", "task is already deleted")
        if self.status == TaskStatus.closed:
            raise InvalidFieldError("status", "cannot delete closed task")
        self.is_active = False


@dataclass
class TaskStop:
    task_id: int
    reason: str
    stopped_at: datetime
    id: int | None = None
    resumed_at: datetime | None = None


@dataclass
class TaskCompletion:
    task_id: int
    actual_quantity: int
    id: int | None = None
    comment: str | None = None
    created_at: datetime | None = None


@dataclass
class TaskCompletionConsumption:
    completion_id: int
    raw_material_id: int
    planned_qty: Decimal
    actual_qty: Decimal
    id: int | None = None
    waste_qty: Decimal | None = None


@dataclass
class RawMaterialReservation:
    stock_id: int
    task_id: int
    quantity: Decimal
    id: int | None = None
    created_at: datetime | None = None


class _RecipeLineProtocol(Protocol):
    raw_material_id: int
    consumption_per_unit: Decimal
    waste_percentage: Decimal


def calculate_material_requirements(
    quantity: int,
    recipe_lines: list[_RecipeLineProtocol],
) -> list[tuple[int, Decimal]]:
    """Return (raw_material_id, planned_qty) for each recipe line.

    planned_qty = quantity × consumption_per_unit × (1 + waste_percentage / 100)
    """
    result = []
    for line in recipe_lines:
        multiplier = Decimal(1) + line.waste_percentage / Decimal(100)
        planned = Decimal(quantity) * line.consumption_per_unit * multiplier
        result.append((line.raw_material_id, planned))
    return result
