from enum import StrEnum


class TaskType(StrEnum):
    order_task = "order_task"
    stock_task = "stock_task"


class TaskStatus(StrEnum):
    created = "created"
    in_progress = "in_progress"
    stopped = "stopped"
    completed = "completed"
    closed = "closed"
