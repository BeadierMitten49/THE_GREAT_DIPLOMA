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
from src.domain.tasks.entities import ProductionTask
from src.domain.tasks.value_objects import TaskStatus, TaskType
from src.infrastructure.db.repositories.references import ProductRepository
from src.infrastructure.db.repositories.tasks import (
    ProductionTaskRepository,
    RawMaterialReservationRepository,
    TaskCompletionRepository,
    TaskStopRepository,
)
from src.infrastructure.db.repositories.warehouse import RawMaterialStockRepository


class ProductionTaskService:
    def __init__(self, session: AsyncSession) -> None:
        self._task_repo = ProductionTaskRepository(session)
        self._stop_repo = TaskStopRepository(session)
        self._completion_repo = TaskCompletionRepository(session)
        self._reservation_repo = RawMaterialReservationRepository(session)
        self._stock_repo = RawMaterialStockRepository(session)
        self._product_repo = ProductRepository(session)

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
        await stop_task(task_id, reason, self._task_repo, self._stop_repo)

    async def resume(self, task_id: int) -> None:
        await resume_task(task_id, self._task_repo, self._stop_repo)

    async def complete(self, dto: CompleteTaskDTO) -> None:
        await complete_task(dto, self._task_repo, self._product_repo, self._completion_repo, self._reservation_repo)

    async def close(self, task_id: int) -> None:
        await close_task(task_id, self._task_repo)

    async def reassign(self, task_id: int, new_executor_id: int) -> None:
        await reassign_task(task_id, new_executor_id, self._task_repo)

    async def delete(self, task_id: int) -> None:
        await delete_task(task_id, self._task_repo, self._reservation_repo)
