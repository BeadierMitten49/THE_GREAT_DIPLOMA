from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.notification_port import INotificationService
from src.domain.notifications.entities import Notification
from src.domain.notifications.value_objects import NotificationEvent
from src.infrastructure.db.repositories.notifications import NotificationRepository
from src.presentation.api.v1.notifications.ws_manager import manager


class DbNotificationService(INotificationService):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def notify(
        self,
        recipient_ids: list[int],
        event_type: NotificationEvent,
        title: str,
        body: str,
        related_entity_type: str | None = None,
        related_entity_id: int | None = None,
    ) -> None:
        repo = NotificationRepository(self._session)
        for recipient_id in recipient_ids:
            notification = Notification(
                recipient_id=recipient_id,
                event_type=event_type,
                title=title,
                body=body,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
            )
            notification_id = await repo.save(notification)

            await manager.send_to_user(recipient_id, {
                "type": "new_notification",
                "notification": {
                    "id": notification_id,
                    "event_type": event_type,
                    "title": title,
                    "body": body,
                    "related_entity_type": related_entity_type,
                    "related_entity_id": related_entity_id,
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            })
