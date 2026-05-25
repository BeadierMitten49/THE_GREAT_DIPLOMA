import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.notification_port import INotificationService
from src.application.ports.telegram_port import ITelegramClient
from src.domain.notifications.entities import Notification
from src.domain.notifications.value_objects import NotificationEvent
from src.infrastructure.db.repositories.auth import UserRepository
from src.infrastructure.db.repositories.notifications import NotificationRepository
from src.presentation.api.v1.notifications.ws_manager import manager

logger = logging.getLogger(__name__)


class DbNotificationService(INotificationService):
    def __init__(
        self,
        session: AsyncSession,
        telegram_client: ITelegramClient | None = None,
    ) -> None:
        self._session = session
        self._telegram_client = telegram_client

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
        user_repo = UserRepository(self._session) if self._telegram_client else None

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

            # WebSocket push
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

            # Telegram push
            if self._telegram_client and user_repo:
                await self._send_telegram(user_repo, recipient_id, title, body)

    async def _send_telegram(
        self,
        user_repo: UserRepository,
        recipient_id: int,
        title: str,
        body: str,
    ) -> None:
        try:
            user = await user_repo.get_by_id(recipient_id)
            if user and user.telegram_id:
                text = f"<b>{title}</b>\n{body}"
                await self._telegram_client.send_message(user.telegram_id, text)
        except Exception:
            logger.exception("Failed to send Telegram to user_id=%d", recipient_id)
