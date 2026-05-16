from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.session import get_session
from src.presentation.api.v1.tasks.service import ProductionTaskService


def get_task_service(session: AsyncSession = Depends(get_session)) -> ProductionTaskService:
    return ProductionTaskService(session)
