from datetime import datetime

from pydantic import BaseModel

from src.domain.notifications.value_objects import NotificationEvent


class NotificationResponse(BaseModel):
    id: int
    recipient_id: int
    event_type: NotificationEvent
    title: str
    body: str
    is_read: bool
    related_entity_type: str | None
    related_entity_id: int | None
    created_at: datetime


class UnreadCountResponse(BaseModel):
    count: int
