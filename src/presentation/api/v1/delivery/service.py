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
from src.domain.delivery.entities import Delivery
from src.domain.delivery.value_objects import DeliveryStatus
from src.infrastructure.db.repositories.delivery import DeliveryRepository


class DeliveryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = DeliveryRepository(session)

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
        await complete_delivery(delivery_id, self._repo)

    async def cancel(self, delivery_id: int, reason: str) -> None:
        await cancel_delivery(delivery_id, reason, self._repo)
