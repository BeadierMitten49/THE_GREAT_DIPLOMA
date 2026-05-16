from abc import abstractmethod

from src.domain.shared.repository import IPlainRepository, ISoftDeleteRepository
from src.domain.tasks.entities import (
    ProductionTask,
    RawMaterialReservation,
    TaskCompletion,
    TaskCompletionConsumption,
    TaskStop,
)
from src.domain.tasks.value_objects import TaskStatus


class IProductionTaskRepository(ISoftDeleteRepository[ProductionTask]):
    @abstractmethod
    async def get_by_status(self, status: TaskStatus) -> list[ProductionTask]: ...

    @abstractmethod
    async def get_by_executor(self, executor_id: int) -> list[ProductionTask]: ...

    @abstractmethod
    async def get_by_order(self, order_id: int) -> list[ProductionTask]: ...


class ITaskStopRepository(IPlainRepository[TaskStop]):
    @abstractmethod
    async def get_by_task(self, task_id: int) -> list[TaskStop]: ...

    @abstractmethod
    async def get_open_stop(self, task_id: int) -> TaskStop | None: ...


class ITaskCompletionRepository(IPlainRepository[TaskCompletion]):
    @abstractmethod
    async def get_by_task(self, task_id: int) -> TaskCompletion | None: ...

    @abstractmethod
    async def get_consumptions(self, completion_id: int) -> list[TaskCompletionConsumption]: ...

    @abstractmethod
    async def save_consumption(self, consumption: TaskCompletionConsumption) -> int: ...


class IRawMaterialReservationRepository(IPlainRepository[RawMaterialReservation]):
    @abstractmethod
    async def get_by_task(self, task_id: int) -> list[RawMaterialReservation]: ...

    @abstractmethod
    async def get_by_stock(self, stock_id: int) -> list[RawMaterialReservation]: ...

    @abstractmethod
    async def delete_by_task(self, task_id: int) -> None: ...
