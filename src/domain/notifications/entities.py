from dataclasses import dataclass
from datetime import datetime

from src.domain.notifications.value_objects import NotificationEvent


@dataclass
class Notification:
    recipient_id: int
    event_type: NotificationEvent
    title: str
    body: str
    is_read: bool = False
    related_entity_type: str | None = None
    related_entity_id: int | None = None
    id: int | None = None
    created_at: datetime | None = None
