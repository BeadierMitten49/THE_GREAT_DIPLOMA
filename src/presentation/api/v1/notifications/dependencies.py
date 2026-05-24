from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.session import get_session
from src.presentation.api.v1.notifications.service import NotificationService


def get_notification_service(session: AsyncSession = Depends(get_session)) -> NotificationService:
    return NotificationService(session)
