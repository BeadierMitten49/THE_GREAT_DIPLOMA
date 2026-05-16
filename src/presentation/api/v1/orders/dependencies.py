from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.session import get_session
from src.presentation.api.v1.orders.service import OrderService


def get_order_service(session: AsyncSession = Depends(get_session)) -> OrderService:
    return OrderService(session)
