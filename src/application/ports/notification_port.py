from abc import ABC, abstractmethod

from src.domain.notifications.value_objects import NotificationEvent


class INotificationService(ABC):
    @abstractmethod
    async def notify(
        self,
        recipient_ids: list[int],
        event_type: NotificationEvent,
        title: str,
        body: str,
        related_entity_type: str | None = None,
        related_entity_id: int | None = None,
    ) -> None: ...
