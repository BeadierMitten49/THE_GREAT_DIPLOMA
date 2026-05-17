from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.session import get_session
from src.presentation.api.v1.delivery.service import DeliveryService


def get_delivery_service(session: AsyncSession = Depends(get_session)) -> DeliveryService:
    return DeliveryService(session)
