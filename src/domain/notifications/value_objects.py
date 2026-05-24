from enum import StrEnum


class NotificationEvent(StrEnum):
    task_completed = "task_completed"
    task_stopped = "task_stopped"
    task_reassigned = "task_reassigned"
    critical_stock = "critical_stock"
    order_shipped = "order_shipped"
    delivery_cancelled = "delivery_cancelled"
    delivery_completed = "delivery_completed"
    warehouse_ops_done = "warehouse_ops_done"
