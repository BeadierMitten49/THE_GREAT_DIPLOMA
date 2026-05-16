from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tasks.entities import (
    ProductionTask,
    RawMaterialReservation,
    TaskCompletion,
    TaskCompletionConsumption,
    TaskStop,
)
from src.domain.tasks.value_objects import TaskStatus, TaskType
from src.infrastructure.db.repositories.tasks import (
    ProductionTaskRepository,
    RawMaterialReservationRepository,
    TaskCompletionRepository,
    TaskStopRepository,
)

pytestmark = pytest.mark.integration


def _make_task(**kwargs) -> ProductionTask:
    defaults = dict(
        product_id=1,
        quantity=100,
        executor_id=2,
        start_date=date(2026, 6, 1),
        deadline=date(2026, 6, 10),
        task_type=TaskType.stock_task,
    )
    defaults.update(kwargs)
    return ProductionTask(**defaults)


# ---------------------------------------------------------------------------
# ProductionTaskRepository
# ---------------------------------------------------------------------------


class TestProductionTaskRepository:
    async def test_save_and_get_by_id(self, session: AsyncSession) -> None:
        repo = ProductionTaskRepository(session)
        task = _make_task()
        task_id = await repo.save(task)
        fetched = await repo.get_by_id(task_id)
        assert fetched is not None
        assert fetched.product_id == 1
        assert fetched.status == TaskStatus.created

    async def test_get_all_returns_active_only(self, session: AsyncSession) -> None:
        repo = ProductionTaskRepository(session)
        t1 = _make_task()
        t2 = _make_task()
        t2.is_active = False
        await repo.save(t1)
        await repo.save(t2)
        result = await repo.get_all()
        assert len(result) == 1

    async def test_get_all_include_inactive(self, session: AsyncSession) -> None:
        repo = ProductionTaskRepository(session)
        t1 = _make_task()
        t2 = _make_task()
        t2.is_active = False
        await repo.save(t1)
        await repo.save(t2)
        result = await repo.get_all(include_inactive=True)
        assert len(result) == 2

    async def test_soft_delete_via_save(self, session: AsyncSession) -> None:
        repo = ProductionTaskRepository(session)
        task = _make_task()
        tid = await repo.save(task)
        task.delete()
        await repo.save(task)
        fetched = await repo.get_by_id(tid)
        assert fetched is not None
        assert fetched.is_active is False

    async def test_get_by_status(self, session: AsyncSession) -> None:
        repo = ProductionTaskRepository(session)
        t1 = _make_task()
        t2 = _make_task()
        await repo.save(t1)
        await repo.save(t2)
        t1.start()
        await repo.save(t1)
        result = await repo.get_by_status(TaskStatus.in_progress)
        assert len(result) == 1
        assert result[0].status == TaskStatus.in_progress

    async def test_get_by_executor(self, session: AsyncSession) -> None:
        repo = ProductionTaskRepository(session)
        await repo.save(_make_task(executor_id=10))
        await repo.save(_make_task(executor_id=20))
        result = await repo.get_by_executor(10)
        assert len(result) == 1
        assert result[0].executor_id == 10

    async def test_get_by_order(self, session: AsyncSession) -> None:
        repo = ProductionTaskRepository(session)
        await repo.save(_make_task(order_id=5, task_type=TaskType.order_task))
        await repo.save(_make_task())
        result = await repo.get_by_order(5)
        assert len(result) == 1
        assert result[0].order_id == 5

    async def test_update_status(self, session: AsyncSession) -> None:
        repo = ProductionTaskRepository(session)
        task = _make_task()
        tid = await repo.save(task)
        task.start()
        await repo.save(task)
        fetched = await repo.get_by_id(tid)
        assert fetched.status == TaskStatus.in_progress
        assert fetched.actual_start_at is not None


# ---------------------------------------------------------------------------
# TaskStopRepository
# ---------------------------------------------------------------------------


class TestTaskStopRepository:
    async def test_save_and_get_by_id(self, session: AsyncSession) -> None:
        repo = TaskStopRepository(session)
        ts = TaskStop(task_id=1, reason="machine broke", stopped_at=datetime.now(timezone.utc))
        sid = await repo.save(ts)
        fetched = await repo.get_by_id(sid)
        assert fetched is not None
        assert fetched.reason == "machine broke"
        assert fetched.resumed_at is None

    async def test_get_by_task(self, session: AsyncSession) -> None:
        repo = TaskStopRepository(session)
        await repo.save(TaskStop(task_id=1, reason="r1", stopped_at=datetime.now(timezone.utc)))
        await repo.save(TaskStop(task_id=1, reason="r2", stopped_at=datetime.now(timezone.utc)))
        await repo.save(TaskStop(task_id=2, reason="r3", stopped_at=datetime.now(timezone.utc)))
        result = await repo.get_by_task(1)
        assert len(result) == 2

    async def test_get_open_stop_returns_open(self, session: AsyncSession) -> None:
        repo = TaskStopRepository(session)
        await repo.save(TaskStop(task_id=1, reason="open", stopped_at=datetime.now(timezone.utc)))
        result = await repo.get_open_stop(1)
        assert result is not None
        assert result.resumed_at is None

    async def test_get_open_stop_returns_none_when_resumed(self, session: AsyncSession) -> None:
        repo = TaskStopRepository(session)
        ts = TaskStop(task_id=1, reason="r", stopped_at=datetime.now(timezone.utc))
        sid = await repo.save(ts)
        ts.resumed_at = datetime.now(timezone.utc)
        await repo.save(ts)
        result = await repo.get_open_stop(1)
        assert result is None

    async def test_get_open_stop_returns_none_when_no_stops(self, session: AsyncSession) -> None:
        repo = TaskStopRepository(session)
        result = await repo.get_open_stop(999)
        assert result is None


# ---------------------------------------------------------------------------
# TaskCompletionRepository
# ---------------------------------------------------------------------------


class TestTaskCompletionRepository:
    async def test_save_and_get_by_id(self, session: AsyncSession) -> None:
        repo = TaskCompletionRepository(session)
        tc = TaskCompletion(task_id=1, actual_quantity=200, comment="good")
        cid = await repo.save(tc)
        fetched = await repo.get_by_id(cid)
        assert fetched is not None
        assert fetched.actual_quantity == 200
        assert fetched.comment == "good"

    async def test_get_by_task(self, session: AsyncSession) -> None:
        repo = TaskCompletionRepository(session)
        await repo.save(TaskCompletion(task_id=1, actual_quantity=100))
        result = await repo.get_by_task(1)
        assert result is not None
        assert result.task_id == 1

    async def test_get_by_task_returns_none_when_missing(self, session: AsyncSession) -> None:
        repo = TaskCompletionRepository(session)
        result = await repo.get_by_task(999)
        assert result is None

    async def test_get_consumptions(self, session: AsyncSession) -> None:
        repo = TaskCompletionRepository(session)
        tc = TaskCompletion(task_id=1, actual_quantity=100)
        cid = await repo.save(tc)
        c1 = TaskCompletionConsumption(
            completion_id=cid, raw_material_id=1,
            planned_qty=Decimal("50"), actual_qty=Decimal("48"),
        )
        c2 = TaskCompletionConsumption(
            completion_id=cid, raw_material_id=2,
            planned_qty=Decimal("10"), actual_qty=Decimal("10"),
        )
        await repo.save_consumption(c1)
        await repo.save_consumption(c2)
        result = await repo.get_consumptions(cid)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# RawMaterialReservationRepository
# ---------------------------------------------------------------------------


class TestRawMaterialReservationRepository:
    async def test_save_and_get_by_id(self, session: AsyncSession) -> None:
        repo = RawMaterialReservationRepository(session)
        r = RawMaterialReservation(stock_id=1, task_id=1, quantity=Decimal("10.5"))
        rid = await repo.save(r)
        fetched = await repo.get_by_id(rid)
        assert fetched is not None
        assert fetched.quantity == Decimal("10.5")

    async def test_get_by_task(self, session: AsyncSession) -> None:
        repo = RawMaterialReservationRepository(session)
        await repo.save(RawMaterialReservation(stock_id=1, task_id=1, quantity=Decimal("5")))
        await repo.save(RawMaterialReservation(stock_id=2, task_id=1, quantity=Decimal("3")))
        await repo.save(RawMaterialReservation(stock_id=1, task_id=2, quantity=Decimal("7")))
        result = await repo.get_by_task(1)
        assert len(result) == 2

    async def test_get_by_stock(self, session: AsyncSession) -> None:
        repo = RawMaterialReservationRepository(session)
        await repo.save(RawMaterialReservation(stock_id=5, task_id=1, quantity=Decimal("5")))
        await repo.save(RawMaterialReservation(stock_id=5, task_id=2, quantity=Decimal("3")))
        await repo.save(RawMaterialReservation(stock_id=6, task_id=3, quantity=Decimal("1")))
        result = await repo.get_by_stock(5)
        assert len(result) == 2

    async def test_delete_by_task(self, session: AsyncSession) -> None:
        repo = RawMaterialReservationRepository(session)
        await repo.save(RawMaterialReservation(stock_id=1, task_id=10, quantity=Decimal("5")))
        await repo.save(RawMaterialReservation(stock_id=2, task_id=10, quantity=Decimal("3")))
        await repo.save(RawMaterialReservation(stock_id=1, task_id=20, quantity=Decimal("1")))
        await repo.delete_by_task(10)
        remaining = await repo.get_by_task(10)
        assert remaining == []
        other = await repo.get_by_task(20)
        assert len(other) == 1
