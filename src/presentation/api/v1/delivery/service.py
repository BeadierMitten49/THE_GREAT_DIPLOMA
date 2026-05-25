from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.delivery.dto import CreateDeliveryDTO
from src.application.delivery.use_cases import (
    cancel_delivery,
    complete_delivery,
    create_delivery,
    get_deliveries,
    get_delivery,
    pick_up_order,
    start_delivery,
)
from src.domain.auth.value_objects import Role
from src.domain.delivery.entities import Delivery
from src.domain.delivery.value_objects import DeliveryStatus
from src.infrastructure.db.repositories.auth import UserRepository
from src.infrastructure.db.repositories.delivery import DeliveryRepository
from src.infrastructure.notifications.service import DbNotificationService
from src.infrastructure.telegram import get_telegram_client


class DeliveryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = DeliveryRepository(session)
        self._user_repo = UserRepository(session)
        self._notification_service = DbNotificationService(session, get_telegram_client())

    async def _get_director_ids(self) -> list[int]:
        users = await self._user_repo.get_all()
        return [u.id for u in users if u.has_role(Role.director)]

    async def get(self, delivery_id: int) -> Delivery:
        return await get_delivery(delivery_id, self._repo)

    async def get_all(
        self,
        executor_id: int | None = None,
        status: DeliveryStatus | None = None,
    ) -> list[Delivery]:
        return await get_deliveries(self._repo, executor_id=executor_id, status=status)

    async def create(self, order_id: int, executor_id: int, planned_date: date) -> int:
        dto = CreateDeliveryDTO(
            order_id=order_id,
            executor_id=executor_id,
            planned_date=planned_date,
        )
        return await create_delivery(dto, self._repo)

    async def pick_up(self, delivery_id: int) -> None:
        await pick_up_order(delivery_id, self._repo)

    async def start(self, delivery_id: int) -> None:
        await start_delivery(delivery_id, self._repo)

    async def complete(self, delivery_id: int) -> None:
        director_ids = await self._get_director_ids()
        await complete_delivery(
            delivery_id, self._repo,
            notification_service=self._notification_service,
            director_ids=director_ids,
        )

    async def cancel(self, delivery_id: int, reason: str) -> None:
        director_ids = await self._get_director_ids()
        await cancel_delivery(
            delivery_id, reason, self._repo,
            notification_service=self._notification_service,
            director_ids=director_ids,
        )
