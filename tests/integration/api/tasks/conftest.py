from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.application.shared.exceptions import NotFoundError
from src.application.tasks.dto import CompleteTaskDTO
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.domain.shared.exceptions import InvalidFieldError
from src.domain.tasks.entities import ProductionTask
from src.domain.tasks.value_objects import TaskStatus, TaskType
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.tasks.dependencies import get_task_service


class FakeProductionTaskService:
    def __init__(self) -> None:
        self._tasks: dict[int, ProductionTask] = {}
        self._next_id = 1

    def _make_task(self, **kwargs) -> ProductionTask:
        defaults = dict(
            product_id=1,
            quantity=100,
            executor_id=2,
            start_date=date(2026, 6, 1),
            deadline=date(2026, 6, 10),
            task_type=TaskType.stock_task,
        )
        defaults.update(kwargs)
        t = ProductionTask(**defaults)
        t.id = self._next_id
        self._next_id += 1
        return t

    async def get(self, task_id: int) -> ProductionTask:
        task = self._tasks.get(task_id)
        if task is None:
            raise NotFoundError("ProductionTask", task_id)
        return task

    async def get_all(
        self,
        status: TaskStatus | None = None,
        executor_id: int | None = None,
    ) -> list[ProductionTask]:
        tasks = [t for t in self._tasks.values() if t.is_active]
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        if executor_id is not None:
            tasks = [t for t in tasks if t.executor_id == executor_id]
        return tasks

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
        task = self._make_task(
            product_id=product_id,
            quantity=quantity,
            executor_id=executor_id,
            start_date=start_date,
            deadline=deadline,
            task_type=task_type,
            order_id=order_id,
            comment=comment,
        )
        self._tasks[task.id] = task
        return task.id, []

    async def start(self, task_id: int) -> None:
        task = await self.get(task_id)
        task.start()

    async def stop(self, task_id: int, reason: str) -> None:
        task = await self.get(task_id)
        task.stop()

    async def resume(self, task_id: int) -> None:
        task = await self.get(task_id)
        task.resume()

    async def complete(self, dto: CompleteTaskDTO) -> None:
        task = await self.get(dto.task_id)
        task.complete()

    async def close(self, task_id: int) -> None:
        task = await self.get(task_id)
        task.close()

    async def reassign(self, task_id: int, new_executor_id: int) -> None:
        task = await self.get(task_id)
        if task.status == TaskStatus.closed:
            raise InvalidFieldError("status", "cannot reassign closed task")
        task.executor_id = new_executor_id

    async def delete(self, task_id: int) -> None:
        task = await self.get(task_id)
        task.delete()


def _make_director() -> User:
    return User(username="director", full_name="Director", roles=[Role.director], id=1)


def _make_production_user() -> User:
    return User(username="worker", full_name="Worker", roles=[Role.production], id=2)


@pytest.fixture
def task_svc() -> FakeProductionTaskService:
    return FakeProductionTaskService()


@pytest_asyncio.fixture
async def client(task_svc: FakeProductionTaskService) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: _make_director()
    app.dependency_overrides[get_task_service] = lambda: task_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def production_client(task_svc: FakeProductionTaskService) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: _make_production_user()
    app.dependency_overrides[get_task_service] = lambda: task_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def saved_task_id(client: AsyncClient) -> int:
    r = await client.post("/api/v1/tasks", json={
        "product_id": 1,
        "quantity": 100,
        "executor_id": 2,
        "start_date": "2026-06-01",
        "deadline": "2026-06-10",
        "task_type": "stock_task",
    })
    return r.json()["id"]
