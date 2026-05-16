from sqlalchemy import delete, select

from src.domain.tasks.entities import (
    ProductionTask,
    RawMaterialReservation,
    TaskCompletion,
    TaskCompletionConsumption,
    TaskStop,
)
from src.domain.tasks.interfaces import (
    IProductionTaskRepository,
    IRawMaterialReservationRepository,
    ITaskCompletionRepository,
    ITaskStopRepository,
)
from src.domain.tasks.value_objects import TaskStatus, TaskType
from src.infrastructure.db.models.tasks import (
    ProductionTaskModel,
    RawMaterialReservationModel,
    TaskCompletionConsumptionModel,
    TaskCompletionModel,
    TaskStopModel,
)
from src.infrastructure.db.repositories.base import BasePlainRepository, BaseSoftDeleteRepository


class ProductionTaskRepository(
    BaseSoftDeleteRepository[ProductionTask, ProductionTaskModel],
    IProductionTaskRepository,
):
    @property
    def _model_class(self) -> type[ProductionTaskModel]:
        return ProductionTaskModel

    def _to_entity(self, model: ProductionTaskModel) -> ProductionTask:
        return ProductionTask(
            id=model.id,
            task_type=TaskType(model.task_type),
            product_id=model.product_id,
            quantity=model.quantity,
            executor_id=model.executor_id,
            start_date=model.start_date,
            deadline=model.deadline,
            status=TaskStatus(model.status),
            order_id=model.order_id,
            comment=model.comment,
            is_active=model.is_active,
            created_at=model.created_at,
            actual_start_at=model.actual_start_at,
            actual_end_at=model.actual_end_at,
        )

    def _to_values(self, entity: ProductionTask) -> dict:
        return {
            "task_type": entity.task_type,
            "product_id": entity.product_id,
            "quantity": entity.quantity,
            "executor_id": entity.executor_id,
            "start_date": entity.start_date,
            "deadline": entity.deadline,
            "status": entity.status,
            "order_id": entity.order_id,
            "comment": entity.comment,
            "is_active": entity.is_active,
            "actual_start_at": entity.actual_start_at,
            "actual_end_at": entity.actual_end_at,
        }

    async def get_by_status(self, status: TaskStatus) -> list[ProductionTask]:
        stmt = select(ProductionTaskModel).where(
            ProductionTaskModel.status == status,
            ProductionTaskModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_executor(self, executor_id: int) -> list[ProductionTask]:
        stmt = select(ProductionTaskModel).where(
            ProductionTaskModel.executor_id == executor_id,
            ProductionTaskModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_order(self, order_id: int) -> list[ProductionTask]:
        stmt = select(ProductionTaskModel).where(
            ProductionTaskModel.order_id == order_id,
            ProductionTaskModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]


class TaskStopRepository(BasePlainRepository[TaskStop, TaskStopModel], ITaskStopRepository):
    @property
    def _model_class(self) -> type[TaskStopModel]:
        return TaskStopModel

    def _to_entity(self, model: TaskStopModel) -> TaskStop:
        return TaskStop(
            id=model.id,
            task_id=model.task_id,
            reason=model.reason,
            stopped_at=model.stopped_at,
            resumed_at=model.resumed_at,
        )

    def _to_values(self, entity: TaskStop) -> dict:
        return {
            "task_id": entity.task_id,
            "reason": entity.reason,
            "stopped_at": entity.stopped_at,
            "resumed_at": entity.resumed_at,
        }

    async def get_by_task(self, task_id: int) -> list[TaskStop]:
        stmt = select(TaskStopModel).where(TaskStopModel.task_id == task_id)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_open_stop(self, task_id: int) -> TaskStop | None:
        stmt = select(TaskStopModel).where(
            TaskStopModel.task_id == task_id,
            TaskStopModel.resumed_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_entity(model) if model else None


class TaskCompletionRepository(
    BasePlainRepository[TaskCompletion, TaskCompletionModel],
    ITaskCompletionRepository,
):
    @property
    def _model_class(self) -> type[TaskCompletionModel]:
        return TaskCompletionModel

    def _to_entity(self, model: TaskCompletionModel) -> TaskCompletion:
        return TaskCompletion(
            id=model.id,
            task_id=model.task_id,
            actual_quantity=model.actual_quantity,
            comment=model.comment,
            created_at=model.created_at,
        )

    def _to_values(self, entity: TaskCompletion) -> dict:
        return {
            "task_id": entity.task_id,
            "actual_quantity": entity.actual_quantity,
            "comment": entity.comment,
        }

    async def get_by_task(self, task_id: int) -> TaskCompletion | None:
        stmt = select(TaskCompletionModel).where(TaskCompletionModel.task_id == task_id)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_entity(model) if model else None

    async def get_consumptions(self, completion_id: int) -> list[TaskCompletionConsumption]:
        stmt = select(TaskCompletionConsumptionModel).where(
            TaskCompletionConsumptionModel.completion_id == completion_id
        )
        result = await self._session.execute(stmt)
        return [
            TaskCompletionConsumption(
                id=row.id,
                completion_id=row.completion_id,
                raw_material_id=row.raw_material_id,
                planned_qty=row.planned_qty,
                actual_qty=row.actual_qty,
                waste_qty=row.waste_qty,
            )
            for row in result.scalars().all()
        ]

    async def save_consumption(self, consumption: TaskCompletionConsumption) -> int:
        model = TaskCompletionConsumptionModel(
            completion_id=consumption.completion_id,
            raw_material_id=consumption.raw_material_id,
            planned_qty=consumption.planned_qty,
            actual_qty=consumption.actual_qty,
            waste_qty=consumption.waste_qty,
        )
        self._session.add(model)
        await self._session.flush()
        consumption.id = model.id
        return model.id


class RawMaterialReservationRepository(
    BasePlainRepository[RawMaterialReservation, RawMaterialReservationModel],
    IRawMaterialReservationRepository,
):
    @property
    def _model_class(self) -> type[RawMaterialReservationModel]:
        return RawMaterialReservationModel

    def _to_entity(self, model: RawMaterialReservationModel) -> RawMaterialReservation:
        return RawMaterialReservation(
            id=model.id,
            stock_id=model.stock_id,
            task_id=model.task_id,
            quantity=model.quantity,
            created_at=model.created_at,
        )

    def _to_values(self, entity: RawMaterialReservation) -> dict:
        return {
            "stock_id": entity.stock_id,
            "task_id": entity.task_id,
            "quantity": entity.quantity,
        }

    async def get_by_task(self, task_id: int) -> list[RawMaterialReservation]:
        stmt = select(RawMaterialReservationModel).where(
            RawMaterialReservationModel.task_id == task_id
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_stock(self, stock_id: int) -> list[RawMaterialReservation]:
        stmt = select(RawMaterialReservationModel).where(
            RawMaterialReservationModel.stock_id == stock_id
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def delete_by_task(self, task_id: int) -> None:
        await self._session.execute(
            delete(RawMaterialReservationModel).where(
                RawMaterialReservationModel.task_id == task_id
            )
        )
