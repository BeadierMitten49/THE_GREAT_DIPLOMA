from datetime import date
from decimal import Decimal

import pytest

from src.application.shared.exceptions import NotFoundError
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
from src.domain.shared.exceptions import InvalidFieldError
from src.domain.tasks.entities import ProductionTask, RawMaterialReservation, TaskStop
from src.domain.tasks.value_objects import TaskStatus, TaskType

from tests.unit.application.tasks.conftest import (
    FakeProductionTaskRepository,
    FakeProductRepository,
    FakeProductStockRepository,
    FakeRawMaterialReservationRepository,
    FakeRawMaterialStockRepository,
    FakeTaskCompletionRepository,
    FakeTaskStopRepository,
    _make_product,
    _make_recipe_line,
    _make_stock,
    _make_task,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------


class TestGetTask:
    async def test_returns_task(
        self, task_repo: FakeProductionTaskRepository, saved_task: ProductionTask
    ) -> None:
        result = await get_task(saved_task.id, task_repo)
        assert result.id == saved_task.id

    async def test_not_found_raises(self, task_repo: FakeProductionTaskRepository) -> None:
        with pytest.raises(NotFoundError):
            await get_task(999, task_repo)


# ---------------------------------------------------------------------------
# get_tasks
# ---------------------------------------------------------------------------


class TestGetTasks:
    async def test_returns_all_active(
        self, task_repo: FakeProductionTaskRepository
    ) -> None:
        t1 = _make_task()
        t1.id = None
        t2 = _make_task()
        t2.id = None
        await task_repo.save(t1)
        await task_repo.save(t2)
        result = await get_tasks(task_repo)
        assert len(result) == 2

    async def test_filter_by_status(
        self, task_repo: FakeProductionTaskRepository, saved_task: ProductionTask
    ) -> None:
        result = await get_tasks(task_repo, status=TaskStatus.created)
        assert len(result) == 1
        result = await get_tasks(task_repo, status=TaskStatus.in_progress)
        assert len(result) == 0

    async def test_filter_by_executor(
        self, task_repo: FakeProductionTaskRepository
    ) -> None:
        t1 = _make_task()
        t1.id = None
        t1.executor_id = 10
        t2 = _make_task()
        t2.id = None
        t2.executor_id = 20
        await task_repo.save(t1)
        await task_repo.save(t2)
        result = await get_tasks(task_repo, executor_id=10)
        assert len(result) == 1
        assert result[0].executor_id == 10


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------


class TestCreateTask:
    def _dto(self, **kwargs) -> CreateTaskDTO:
        defaults = dict(
            product_id=1,
            quantity=100,
            executor_id=2,
            start_date=date(2026, 6, 1),
            deadline=date(2026, 6, 10),
            task_type=TaskType.stock_task,
        )
        defaults.update(kwargs)
        return CreateTaskDTO(**defaults)

    async def test_returns_task_id(
        self,
        task_repo: FakeProductionTaskRepository,
        product_repo: FakeProductRepository,
        stock_repo: FakeRawMaterialStockRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        task_id, warnings = await create_task(
            self._dto(), task_repo, product_repo, stock_repo, reservation_repo
        )
        assert isinstance(task_id, int)
        assert task_id > 0

    async def test_task_saved_with_created_status(
        self,
        task_repo: FakeProductionTaskRepository,
        product_repo: FakeProductRepository,
        stock_repo: FakeRawMaterialStockRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        task_id, _ = await create_task(
            self._dto(), task_repo, product_repo, stock_repo, reservation_repo
        )
        task = await task_repo.get_by_id(task_id)
        assert task.status == TaskStatus.created

    async def test_creates_reservations_when_stock_sufficient(
        self,
        task_repo: FakeProductionTaskRepository,
        product_repo: FakeProductRepository,
        stock_repo: FakeRawMaterialStockRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        task_id, warnings = await create_task(
            self._dto(), task_repo, product_repo, stock_repo, reservation_repo
        )
        reservations = await reservation_repo.get_by_task(task_id)
        assert len(reservations) > 0
        assert warnings == []

    async def test_warning_when_stock_insufficient(
        self,
        task_repo: FakeProductionTaskRepository,
        product_repo: FakeProductRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        # Only 10 units available, but 55 needed
        poor_stock = FakeRawMaterialStockRepository(
            batches=[_make_stock(rm_id=1, qty="10")]
        )
        task_id, warnings = await create_task(
            self._dto(), task_repo, product_repo, poor_stock, reservation_repo
        )
        assert len(warnings) > 0
        assert task_id > 0  # task still created

    async def test_no_stock_at_all_still_creates_task(
        self,
        task_repo: FakeProductionTaskRepository,
        product_repo: FakeProductRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        empty_stock = FakeRawMaterialStockRepository(batches=[])
        task_id, warnings = await create_task(
            self._dto(), task_repo, product_repo, empty_stock, reservation_repo
        )
        assert task_id > 0
        assert len(warnings) == 1

    async def test_multiple_batches_allocated_fifo(
        self,
        task_repo: FakeProductionTaskRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        # Need 55 units; two batches of 30 each → allocates from both
        stock = FakeRawMaterialStockRepository(batches=[
            _make_stock(rm_id=1, qty="30"),
            _make_stock(rm_id=1, qty="30"),
        ])
        product_repo = FakeProductRepository(_make_product())
        task_id, warnings = await create_task(
            self._dto(), task_repo, product_repo, stock, reservation_repo
        )
        reservations = await reservation_repo.get_by_task(task_id)
        assert len(reservations) == 2
        total = sum(r.quantity for r in reservations)
        assert total == Decimal("55.0")

    async def test_empty_recipe_no_reservations(
        self,
        task_repo: FakeProductionTaskRepository,
        stock_repo: FakeRawMaterialStockRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        product_repo = FakeProductRepository(_make_product(recipe_lines=[]))
        task_id, warnings = await create_task(
            self._dto(), task_repo, product_repo, stock_repo, reservation_repo
        )
        reservations = await reservation_repo.get_by_task(task_id)
        assert reservations == []
        assert warnings == []


# ---------------------------------------------------------------------------
# start_task
# ---------------------------------------------------------------------------


class TestStartTask:
    async def test_sets_in_progress(
        self, task_repo: FakeProductionTaskRepository, saved_task: ProductionTask
    ) -> None:
        await start_task(saved_task.id, task_repo)
        task = await task_repo.get_by_id(saved_task.id)
        assert task.status == TaskStatus.in_progress

    async def test_not_found_raises(self, task_repo: FakeProductionTaskRepository) -> None:
        with pytest.raises(NotFoundError):
            await start_task(999, task_repo)

    async def test_invalid_transition_raises(
        self, task_repo: FakeProductionTaskRepository, saved_task: ProductionTask
    ) -> None:
        await start_task(saved_task.id, task_repo)
        with pytest.raises(InvalidFieldError):
            await start_task(saved_task.id, task_repo)


# ---------------------------------------------------------------------------
# stop_task
# ---------------------------------------------------------------------------


class TestStopTask:
    async def test_sets_stopped(
        self,
        task_repo: FakeProductionTaskRepository,
        stop_repo: FakeTaskStopRepository,
        saved_task: ProductionTask,
    ) -> None:
        await start_task(saved_task.id, task_repo)
        await stop_task(saved_task.id, "machine broke", task_repo, stop_repo)
        task = await task_repo.get_by_id(saved_task.id)
        assert task.status == TaskStatus.stopped

    async def test_creates_task_stop_record(
        self,
        task_repo: FakeProductionTaskRepository,
        stop_repo: FakeTaskStopRepository,
        saved_task: ProductionTask,
    ) -> None:
        await start_task(saved_task.id, task_repo)
        await stop_task(saved_task.id, "reason", task_repo, stop_repo)
        stops = await stop_repo.get_by_task(saved_task.id)
        assert len(stops) == 1
        assert stops[0].reason == "reason"

    async def test_not_found_raises(
        self, task_repo: FakeProductionTaskRepository, stop_repo: FakeTaskStopRepository
    ) -> None:
        with pytest.raises(NotFoundError):
            await stop_task(999, "r", task_repo, stop_repo)

    async def test_from_created_raises(
        self,
        task_repo: FakeProductionTaskRepository,
        stop_repo: FakeTaskStopRepository,
        saved_task: ProductionTask,
    ) -> None:
        with pytest.raises(InvalidFieldError):
            await stop_task(saved_task.id, "r", task_repo, stop_repo)


# ---------------------------------------------------------------------------
# resume_task
# ---------------------------------------------------------------------------


class TestResumeTask:
    async def test_sets_in_progress(
        self,
        task_repo: FakeProductionTaskRepository,
        stop_repo: FakeTaskStopRepository,
        saved_task: ProductionTask,
    ) -> None:
        await start_task(saved_task.id, task_repo)
        await stop_task(saved_task.id, "r", task_repo, stop_repo)
        await resume_task(saved_task.id, task_repo, stop_repo)
        task = await task_repo.get_by_id(saved_task.id)
        assert task.status == TaskStatus.in_progress

    async def test_closes_open_stop_record(
        self,
        task_repo: FakeProductionTaskRepository,
        stop_repo: FakeTaskStopRepository,
        saved_task: ProductionTask,
    ) -> None:
        await start_task(saved_task.id, task_repo)
        await stop_task(saved_task.id, "r", task_repo, stop_repo)
        await resume_task(saved_task.id, task_repo, stop_repo)
        open_stop = await stop_repo.get_open_stop(saved_task.id)
        assert open_stop is None

    async def test_not_found_raises(
        self, task_repo: FakeProductionTaskRepository, stop_repo: FakeTaskStopRepository
    ) -> None:
        with pytest.raises(NotFoundError):
            await resume_task(999, task_repo, stop_repo)

    async def test_from_in_progress_raises(
        self,
        task_repo: FakeProductionTaskRepository,
        stop_repo: FakeTaskStopRepository,
        saved_task: ProductionTask,
    ) -> None:
        await start_task(saved_task.id, task_repo)
        with pytest.raises(InvalidFieldError):
            await resume_task(saved_task.id, task_repo, stop_repo)


# ---------------------------------------------------------------------------
# complete_task
# ---------------------------------------------------------------------------


class TestCompleteTask:
    def _dto(self, task_id: int, **kwargs) -> CompleteTaskDTO:
        defaults = dict(
            task_id=task_id,
            actual_quantity=95,
            consumptions=[ConsumptionInputDTO(raw_material_id=1, actual_qty=Decimal("48"))],
        )
        defaults.update(kwargs)
        return CompleteTaskDTO(**defaults)

    async def test_sets_completed(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        saved_task: ProductionTask,
    ) -> None:
        product_repo = FakeProductRepository(_make_product())
        await start_task(saved_task.id, task_repo)
        await complete_task(self._dto(saved_task.id), task_repo, product_repo, completion_repo, reservation_repo)
        task = await task_repo.get_by_id(saved_task.id)
        assert task.status == TaskStatus.completed

    async def test_creates_completion_record(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        saved_task: ProductionTask,
    ) -> None:
        product_repo = FakeProductRepository(_make_product())
        await start_task(saved_task.id, task_repo)
        await complete_task(self._dto(saved_task.id), task_repo, product_repo, completion_repo, reservation_repo)
        completion = await completion_repo.get_by_task(saved_task.id)
        assert completion is not None
        assert completion.actual_quantity == 95

    async def test_creates_consumption_records(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        saved_task: ProductionTask,
    ) -> None:
        product_repo = FakeProductRepository(_make_product())
        await start_task(saved_task.id, task_repo)
        await complete_task(self._dto(saved_task.id), task_repo, product_repo, completion_repo, reservation_repo)
        completion = await completion_repo.get_by_task(saved_task.id)
        consumptions = await completion_repo.get_consumptions(completion.id)
        assert len(consumptions) == 1
        assert consumptions[0].actual_qty == Decimal("48")

    async def test_releases_reservations(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        saved_task: ProductionTask,
    ) -> None:
        product_repo = FakeProductRepository(_make_product())
        await reservation_repo.save(
            RawMaterialReservation(stock_id=1, task_id=saved_task.id, quantity=Decimal("55"))
        )
        await start_task(saved_task.id, task_repo)
        await complete_task(self._dto(saved_task.id), task_repo, product_repo, completion_repo, reservation_repo)
        remaining = await reservation_repo.get_by_task(saved_task.id)
        assert remaining == []

    async def test_not_found_raises(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        product_repo = FakeProductRepository(_make_product())
        with pytest.raises(NotFoundError):
            await complete_task(self._dto(999), task_repo, product_repo, completion_repo, reservation_repo)

    async def test_from_stopped_raises(
        self,
        task_repo: FakeProductionTaskRepository,
        stop_repo: FakeTaskStopRepository,
        completion_repo: FakeTaskCompletionRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        saved_task: ProductionTask,
    ) -> None:
        product_repo = FakeProductRepository(_make_product())
        await start_task(saved_task.id, task_repo)
        await stop_task(saved_task.id, "r", task_repo, stop_repo)
        with pytest.raises(InvalidFieldError):
            await complete_task(self._dto(saved_task.id), task_repo, product_repo, completion_repo, reservation_repo)


# ---------------------------------------------------------------------------
# close_task
# ---------------------------------------------------------------------------


class TestCloseTask:
    async def test_sets_closed_and_creates_product_stock(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        stock_repo: FakeRawMaterialStockRepository,
        product_stock_repo: FakeProductStockRepository,
        saved_task: ProductionTask,
    ) -> None:
        product_repo = FakeProductRepository(_make_product())
        await start_task(saved_task.id, task_repo)
        dto = CompleteTaskDTO(
            task_id=saved_task.id, actual_quantity=90,
            consumptions=[ConsumptionInputDTO(raw_material_id=1, actual_qty=Decimal("45"))],
        )
        await complete_task(dto, task_repo, product_repo, completion_repo, reservation_repo)
        await close_task(
            saved_task.id, task_repo,
            completion_repo=completion_repo,
            product_stock_repo=product_stock_repo,
            raw_material_stock_repo=stock_repo,
        )
        task = await task_repo.get_by_id(saved_task.id)
        assert task.status == TaskStatus.closed
        # product stock created
        ps = await product_stock_repo.get_all()
        assert len(ps) == 1
        assert ps[0].quantity == 90
        # raw material written off
        rm_batches = await stock_repo.get_by_raw_material(1)
        assert rm_batches[0].quantity == Decimal("55")  # 100 - 45

    async def test_not_found_raises(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        product_stock_repo: FakeProductStockRepository,
        stock_repo: FakeRawMaterialStockRepository,
    ) -> None:
        with pytest.raises(NotFoundError):
            await close_task(
                999, task_repo,
                completion_repo=completion_repo,
                product_stock_repo=product_stock_repo,
                raw_material_stock_repo=stock_repo,
            )

    async def test_from_in_progress_raises(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        product_stock_repo: FakeProductStockRepository,
        stock_repo: FakeRawMaterialStockRepository,
        saved_task: ProductionTask,
    ) -> None:
        await start_task(saved_task.id, task_repo)
        with pytest.raises(InvalidFieldError):
            await close_task(
                saved_task.id, task_repo,
                completion_repo=completion_repo,
                product_stock_repo=product_stock_repo,
                raw_material_stock_repo=stock_repo,
            )


# ---------------------------------------------------------------------------
# reassign_task
# ---------------------------------------------------------------------------


class TestReassignTask:
    async def test_changes_executor(
        self, task_repo: FakeProductionTaskRepository, saved_task: ProductionTask
    ) -> None:
        await reassign_task(saved_task.id, 99, task_repo)
        task = await task_repo.get_by_id(saved_task.id)
        assert task.executor_id == 99

    async def test_not_found_raises(self, task_repo: FakeProductionTaskRepository) -> None:
        with pytest.raises(NotFoundError):
            await reassign_task(999, 5, task_repo)

    async def test_closed_task_raises(
        self,
        task_repo: FakeProductionTaskRepository,
        completion_repo: FakeTaskCompletionRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        stock_repo: FakeRawMaterialStockRepository,
        product_stock_repo: FakeProductStockRepository,
        saved_task: ProductionTask,
    ) -> None:
        product_repo = FakeProductRepository(_make_product())
        await start_task(saved_task.id, task_repo)
        dto = CompleteTaskDTO(
            task_id=saved_task.id, actual_quantity=90,
            consumptions=[ConsumptionInputDTO(raw_material_id=1, actual_qty=Decimal("45"))],
        )
        await complete_task(dto, task_repo, product_repo, completion_repo, reservation_repo)
        await close_task(
            saved_task.id, task_repo,
            completion_repo=completion_repo,
            product_stock_repo=product_stock_repo,
            raw_material_stock_repo=stock_repo,
        )
        with pytest.raises(InvalidFieldError):
            await reassign_task(saved_task.id, 99, task_repo)


# ---------------------------------------------------------------------------
# delete_task
# ---------------------------------------------------------------------------


class TestDeleteTask:
    async def test_soft_deletes_task(
        self,
        task_repo: FakeProductionTaskRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        saved_task: ProductionTask,
    ) -> None:
        await delete_task(saved_task.id, task_repo, reservation_repo)
        task = await task_repo.get_by_id(saved_task.id)
        assert task.is_active is False

    async def test_releases_reservations_on_delete(
        self,
        task_repo: FakeProductionTaskRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
        saved_task: ProductionTask,
    ) -> None:
        await reservation_repo.save(
            RawMaterialReservation(stock_id=1, task_id=saved_task.id, quantity=Decimal("20"))
        )
        await delete_task(saved_task.id, task_repo, reservation_repo)
        remaining = await reservation_repo.get_by_task(saved_task.id)
        assert remaining == []

    async def test_not_found_raises(
        self,
        task_repo: FakeProductionTaskRepository,
        reservation_repo: FakeRawMaterialReservationRepository,
    ) -> None:
        with pytest.raises(NotFoundError):
            await delete_task(999, task_repo, reservation_repo)
