from sqlalchemy.ext.asyncio import AsyncSession

from src.application.notifications.use_cases import (
    get_recent_notifications,
    get_unread_count,
    get_user_notifications,
    mark_all_read,
    mark_read,
)
from src.domain.notifications.entities import Notification
from src.infrastructure.db.repositories.notifications import NotificationRepository


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = NotificationRepository(session)

    async def get_my_notifications(
        self, user_id: int, *, unread_only: bool = False,
    ) -> list[Notification]:
        return await get_user_notifications(user_id, self._repo, unread_only=unread_only)

    async def get_recent(self, limit: int = 20) -> list[Notification]:
        return await get_recent_notifications(self._repo, limit)

    async def get_unread_count(self, user_id: int) -> int:
        return await get_unread_count(user_id, self._repo)

    async def mark_read(self, notification_id: int) -> None:
        return await mark_read(notification_id, self._repo)

    async def mark_all_read(self, user_id: int) -> None:
        return await mark_all_read(user_id, self._repo)
