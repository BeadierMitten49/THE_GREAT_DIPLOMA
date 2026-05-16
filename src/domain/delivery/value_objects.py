from enum import StrEnum


class DeliveryStatus(StrEnum):
    pending = "pending"
    picked_up = "picked_up"
    in_transit = "in_transit"
    completed = "completed"
    cancelled = "cancelled"
