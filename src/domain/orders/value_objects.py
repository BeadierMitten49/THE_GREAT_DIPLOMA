from enum import StrEnum


class OrderStatus(StrEnum):
    created = "created"
    production = "production"
    assembly = "assembly"
    delivery = "delivery"
    completed = "completed"
