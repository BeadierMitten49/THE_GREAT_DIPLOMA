from dataclasses import dataclass
from datetime import date, datetime, timezone

from src.domain.delivery.value_objects import DeliveryStatus
from src.domain.shared.exceptions import InvalidFieldError


@dataclass
class Delivery:
    order_id: int
    executor_id: int
    planned_date: date
    status: DeliveryStatus = DeliveryStatus.pending
    id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancellation_reason: str | None = None

    def pick_up(self) -> None:
        if self.status != DeliveryStatus.pending:
            raise InvalidFieldError("status", f"cannot pick up delivery in status '{self.status}'")
        self.status = DeliveryStatus.picked_up

    def start(self) -> None:
        if self.status != DeliveryStatus.picked_up:
            raise InvalidFieldError("status", f"cannot start delivery in status '{self.status}'")
        self.status = DeliveryStatus.in_transit
        self.started_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        if self.status != DeliveryStatus.in_transit:
            raise InvalidFieldError("status", f"cannot complete delivery in status '{self.status}'")
        self.status = DeliveryStatus.completed
        self.completed_at = datetime.now(timezone.utc)

    def cancel(self, reason: str) -> None:
        if not reason:
            raise InvalidFieldError("cancellation_reason", "reason is required")
        if self.status not in (DeliveryStatus.pending, DeliveryStatus.picked_up):
            raise InvalidFieldError("status", f"cannot cancel delivery in status '{self.status}'")
        self.status = DeliveryStatus.cancelled
        self.cancellation_reason = reason
1