from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CreateDeliveryDTO:
    order_id: int
    executor_id: int
    planned_date: date
