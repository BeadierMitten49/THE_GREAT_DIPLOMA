from src.domain.notifications.entities import Notification
from src.domain.notifications.interfaces import INotificationRepository
from src.domain.notifications.value_objects import NotificationEvent


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


async def get_user_notifications(
    recipient_id: int,
    repo: INotificationRepository,
    *,
    unread_only: bool = False,
) -> list[Notification]:
    return await repo.get_by_recipient(recipient_id, unread_only=unread_only)


async def get_recent_notifications(
    repo: INotificationRepository,
    limit: int = 20,
) -> list[Notification]:
    return await repo.get_recent(limit)


async def get_unread_count(
    recipient_id: int,
    repo: INotificationRepository,
) -> int:
    unread = await repo.get_by_recipient(recipient_id, unread_only=True)
    return len(unread)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


async def create_notification(
    repo: INotificationRepository,
    *,
    recipient_id: int,
    event_type: NotificationEvent,
    title: str,
    body: str,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> int:
    notification = Notification(
        recipient_id=recipient_id,
        event_type=event_type,
        title=title,
        body=body,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    return await repo.save(notification)


async def mark_read(
    notification_id: int,
    repo: INotificationRepository,
) -> None:
    await repo.mark_as_read(notification_id)


async def mark_all_read(
    recipient_id: int,
    repo: INotificationRepository,
) -> None:
    await repo.mark_all_as_read(recipient_id)
