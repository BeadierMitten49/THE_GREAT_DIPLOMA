from sqlalchemy import select

from src.domain.delivery.entities import Delivery
from src.domain.delivery.interfaces import IDeliveryRepository
from src.domain.delivery.value_objects import DeliveryStatus
from src.infrastructure.db.models.delivery import DeliveryModel
from src.infrastructure.db.repositories.base import BasePlainRepository


class DeliveryRepository(BasePlainRepository[Delivery, DeliveryModel], IDeliveryRepository):
    @property
    def _model_class(self) -> type[DeliveryModel]:
        return DeliveryModel

    def _to_entity(self, model: DeliveryModel) -> Delivery:
        return Delivery(
            id=model.id,
            order_id=model.order_id,
            executor_id=model.executor_id,
            status=DeliveryStatus(model.status),
            planned_date=model.planned_date,
            started_at=model.started_at,
            completed_at=model.completed_at,
            cancellation_reason=model.cancellation_reason,
        )

    def _to_values(self, entity: Delivery) -> dict:
        return {
            "order_id": entity.order_id,
            "executor_id": entity.executor_id,
            "status": entity.status,
            "planned_date": entity.planned_date,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
            "cancellation_reason": entity.cancellation_reason,
        }

    async def get_by_order(self, order_id: int) -> Delivery | None:
        stmt = select(DeliveryModel).where(DeliveryModel.order_id == order_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_executor(self, executor_id: int) -> list[Delivery]:
        stmt = select(DeliveryModel).where(DeliveryModel.executor_id == executor_id)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_status(self, status: DeliveryStatus) -> list[Delivery]:
        stmt = select(DeliveryModel).where(DeliveryModel.status == status)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]
