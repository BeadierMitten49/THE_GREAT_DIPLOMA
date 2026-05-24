from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.tasks.dto import CompleteTaskDTO, ConsumptionInputDTO, CreateTaskDTO
from src.application.tasks.use_cases import (
    close_task,
    complete_task,
    create_task,
    delete_task,
    get_task,
    get_tasks,
    reassign_task,
    resume_task,
    start_task,
    stop_task,
)
from src.domain.auth.value_objects import Role
from src.domain.tasks.entities import ProductionTask
from src.domain.tasks.value_objects import TaskStatus, TaskType
from src.infrastructure.db.repositories.auth import UserRepository
from src.infrastructure.db.repositories.orders import ProductReservationRepository
from src.infrastructure.db.repositories.references import ProductRepository, RawMaterialCatalogRepository
from src.infrastructure.db.repositories.tasks import (
    ProductionTaskRepository,
    RawMaterialReservationRepository,
    TaskCompletionRepository,
    TaskStopRepository,
)
from src.infrastructure.db.repositories.warehouse import ProductStockRepository, RawMaterialStockRepository
from src.infrastructure.notifications.service import DbNotificationService


class ProductionTaskService:
    def __init__(self, session: AsyncSession) -> None:
        self._task_repo = ProductionTaskRepository(session)
        self._stop_repo = TaskStopRepository(session)
        self._completion_repo = TaskCompletionRepository(session)
        self._reservation_repo = RawMaterialReservationRepository(session)
        self._stock_repo = RawMaterialStockRepository(session)
        self._product_repo = ProductRepository(session)
        self._product_stock_repo = ProductStockRepository(session)
        self._product_reservation_repo = ProductReservationRepository(session)
        self._user_repo = UserRepository(session)
        self._rm_catalog_repo = RawMaterialCatalogRepository(session)
        self._notification_service = DbNotificationService(session)

    async def _get_user_ids_by_role(self, role: Role) -> list[int]:
        users = await self._user_repo.get_all()
        return [u.id for u in users if u.has_role(role)]

    async def get(self, task_id: int) -> ProductionTask:
        return await get_task(task_id, self._task_repo)

    async def get_all(
        self,
        status: TaskStatus | None = None,
        executor_id: int | None = None,
    ) -> list[ProductionTask]:
        return await get_tasks(self._task_repo, status=status, executor_id=executor_id)

    async def create(
        self,
        product_id: int,
        quantity: int,
        executor_id: int,
        start_date: date,
        deadline: date,
        task_type: TaskType,
        order_id: int | None,
        comment: str | None,
    ) -> tuple[int, list[int]]:
        dto = CreateTaskDTO(
            product_id=product_id,
            quantity=quantity,
            executor_id=executor_id,
            start_date=start_date,
            deadline=deadline,
            task_type=task_type,
            order_id=order_id,
            comment=comment,
        )
        return await create_task(
            dto, self._task_repo, self._product_repo, self._stock_repo, self._reservation_repo
        )

    async def start(self, task_id: int) -> None:
        await start_task(task_id, self._task_repo)

    async def stop(self, task_id: int, reason: str) -> None:
        await stop_task(
            task_id, reason, self._task_repo, self._stop_repo,
            notification_service=self._notification_service,
        )

    async def resume(self, task_id: int) -> None:
        await resume_task(task_id, self._task_repo, self._stop_repo)

    async def complete(self, dto: CompleteTaskDTO) -> None:
        director_ids = await self._get_user_ids_by_role(Role.director)
        warehouse_ids = await self._get_user_ids_by_role(Role.warehouse)
        await complete_task(
            dto, self._task_repo, self._product_repo, self._completion_repo,
            notification_service=self._notification_service,
            director_ids=director_ids,
            warehouse_ids=warehouse_ids,
        )

    async def close(self, task_id: int) -> None:
        director_ids = await self._get_user_ids_by_role(Role.director)
        await close_task(
            task_id, self._task_repo,
            completion_repo=self._completion_repo,
            product_stock_repo=self._product_stock_repo,
            raw_material_stock_repo=self._stock_repo,
            raw_material_reservation_repo=self._reservation_repo,
            product_reservation_repo=self._product_reservation_repo,
            notification_service=self._notification_service,
            director_ids=director_ids,
        )

    async def reassign(self, task_id: int, new_executor_id: int) -> None:
        await reassign_task(
            task_id, new_executor_id, self._task_repo,
            notification_service=self._notification_service,
        )

    async def delete(self, task_id: int) -> None:
        await delete_task(task_id, self._task_repo, self._reservation_repo)

    async def get_product_name(self, product_id: int) -> str:
        product = await self._product_repo.get_by_id(product_id)
        return product.name if product else f"Продукт #{product_id}"

    async def get_executor_name(self, executor_id: int) -> str:
        user = await self._user_repo.get_by_id(executor_id)
        return user.full_name if user else f"#{executor_id}"

    async def get_drawer_data(self, task_id: int) -> dict:
        task = await self.get(task_id)

        product_name = await self.get_product_name(task.product_id)
        executor_name = await self.get_executor_name(task.executor_id)

        stops_raw = await self._stop_repo.get_by_task(task_id)
        stops = [
            {
                "id": s.id,
                "reason": s.reason,
                "stopped_at": s.stopped_at,
                "resumed_at": s.resumed_at,
            }
            for s in stops_raw
        ]

        completion_data = None
        completion = await self._completion_repo.get_by_task(task_id)
        if completion is not None:
            consumptions_raw = await self._completion_repo.get_consumptions(completion.id)
            consumptions = []
            for c in consumptions_raw:
                rm = await self._rm_catalog_repo.get_by_id(c.raw_material_id)
                consumptions.append({
                    "raw_material_id": c.raw_material_id,
                    "raw_material_name": rm.name if rm else f"#{c.raw_material_id}",
                    "planned_qty": c.planned_qty,
                    "actual_qty": c.actual_qty,
                    "waste_qty": c.waste_qty,
                })
            completion_data = {
                "actual_quantity": completion.actual_quantity,
                "comment": completion.comment,
                "consumptions": consumptions,
            }

        reservations_raw = await self._reservation_repo.get_by_task(task_id)
        reservations = []
        for r in reservations_raw:
            stock = await self._stock_repo.get_by_id(r.stock_id)
            if stock is not None:
                rm = await self._rm_catalog_repo.get_by_id(stock.raw_material_id)
                rm_name = rm.name if rm else f"#{stock.raw_material_id}"
                batch_label = f"С-{stock.arrival_date.year}-{stock.id:03d}"
            else:
                rm_name = "?"
                batch_label = "?"
            reservations.append({
                "id": r.id,
                "stock_id": r.stock_id,
                "raw_material_name": rm_name,
                "quantity": r.quantity,
                "batch_label": batch_label,
            })

        return {
            "task": task,
            "product_name": product_name,
            "executor_name": executor_name,
            "stops": stops,
            "completion": completion_data,
            "reservations": reservations,
        }
