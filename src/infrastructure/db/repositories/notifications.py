from sqlalchemy import select, update

from src.domain.notifications.entities import Notification
from src.domain.notifications.interfaces import INotificationRepository
from src.domain.notifications.value_objects import NotificationEvent
from src.infrastructure.db.models.notifications import NotificationModel
from src.infrastructure.db.repositories.base import BasePlainRepository


class NotificationRepository(BasePlainRepository[Notification, NotificationModel], INotificationRepository):
    @property
    def _model_class(self) -> type[NotificationModel]:
        return NotificationModel

    def _to_entity(self, model: NotificationModel) -> Notification:
        return Notification(
            id=model.id,
            recipient_id=model.recipient_id,
            event_type=NotificationEvent(model.event_type),
            title=model.title,
            body=model.body,
            is_read=model.is_read,
            related_entity_type=model.related_entity_type,
            related_entity_id=model.related_entity_id,
            created_at=model.created_at,
        )

    def _to_values(self, entity: Notification) -> dict:
        return {
            "recipient_id": entity.recipient_id,
            "event_type": entity.event_type,
            "title": entity.title,
            "body": entity.body,
            "is_read": entity.is_read,
            "related_entity_type": entity.related_entity_type,
            "related_entity_id": entity.related_entity_id,
        }

    async def get_by_recipient(
        self, recipient_id: int, *, unread_only: bool = False,
    ) -> list[Notification]:
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.recipient_id == recipient_id)
            .order_by(NotificationModel.created_at.desc())
        )
        if unread_only:
            stmt = stmt.where(NotificationModel.is_read.is_(False))
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def mark_as_read(self, id: int) -> None:
        await self._session.execute(
            update(NotificationModel)
            .where(NotificationModel.id == id)
            .values(is_read=True)
        )

    async def mark_all_as_read(self, recipient_id: int) -> None:
        await self._session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.recipient_id == recipient_id,
                NotificationModel.is_read.is_(False),
            )
            .values(is_read=True)
        )

    async def get_recent(self, limit: int = 20) -> list[Notification]:
        stmt = (
            select(NotificationModel)
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]
