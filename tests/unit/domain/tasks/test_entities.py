from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from src.domain.shared.exceptions import InvalidFieldError
from src.domain.tasks.entities import (
    ProductionTask,
    RawMaterialReservation,
    TaskCompletion,
    TaskCompletionConsumption,
    TaskStop,
    calculate_material_requirements,
)
from src.domain.tasks.value_objects import TaskStatus, TaskType

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class TestTaskType:
    def test_order_task(self) -> None:
        assert TaskType.order_task == "order_task"

    def test_stock_task(self) -> None:
        assert TaskType.stock_task == "stock_task"


class TestTaskStatus:
    def test_all_values(self) -> None:
        assert TaskStatus.created == "created"
        assert TaskStatus.in_progress == "in_progress"
        assert TaskStatus.stopped == "stopped"
        assert TaskStatus.completed == "completed"
        assert TaskStatus.closed == "closed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
# ProductionTask — start
# ---------------------------------------------------------------------------


class TestProductionTaskStart:
    def test_start_sets_in_progress(self) -> None:
        task = _make_task()
        task.start()
        assert task.status == TaskStatus.in_progress

    def test_start_sets_actual_start_at(self) -> None:
        task = _make_task()
        task.start()
        assert task.actual_start_at is not None

    def test_start_from_in_progress_raises(self) -> None:
        task = _make_task()
        task.start()
        with pytest.raises(InvalidFieldError):
            task.start()

    def test_start_from_stopped_raises(self) -> None:
        task = _make_task()
        task.start()
        task.stop()
        with pytest.raises(InvalidFieldError):
            task.start()

    def test_start_from_completed_raises(self) -> None:
        task = _make_task()
        task.start()
        task.complete()
        with pytest.raises(InvalidFieldError):
            task.start()


# ---------------------------------------------------------------------------
# ProductionTask — stop
# ---------------------------------------------------------------------------


class TestProductionTaskStop:
    def test_stop_sets_stopped(self) -> None:
        task = _make_task()
        task.start()
        task.stop()
        assert task.status == TaskStatus.stopped

    def test_stop_from_created_raises(self) -> None:
        task = _make_task()
        with pytest.raises(InvalidFieldError):
            task.stop()

    def test_stop_from_stopped_raises(self) -> None:
        task = _make_task()
        task.start()
        task.stop()
        with pytest.raises(InvalidFieldError):
            task.stop()

    def test_stop_from_completed_raises(self) -> None:
        task = _make_task()
        task.start()
        task.complete()
        with pytest.raises(InvalidFieldError):
            task.stop()


# ---------------------------------------------------------------------------
# ProductionTask — resume
# ---------------------------------------------------------------------------


class TestProductionTaskResume:
    def test_resume_sets_in_progress(self) -> None:
        task = _make_task()
        task.start()
        task.stop()
        task.resume()
        assert task.status == TaskStatus.in_progress

    def test_resume_from_created_raises(self) -> None:
        task = _make_task()
        with pytest.raises(InvalidFieldError):
            task.resume()

    def test_resume_from_in_progress_raises(self) -> None:
        task = _make_task()
        task.start()
        with pytest.raises(InvalidFieldError):
            task.resume()

    def test_resume_multiple_times(self) -> None:
        task = _make_task()
        task.start()
        task.stop()
        task.resume()
        task.stop()
        task.resume()
        assert task.status == TaskStatus.in_progress


# ---------------------------------------------------------------------------
# ProductionTask — complete
# ---------------------------------------------------------------------------


class TestProductionTaskComplete:
    def test_complete_sets_completed(self) -> None:
        task = _make_task()
        task.start()
        task.complete()
        assert task.status == TaskStatus.completed

    def test_complete_sets_actual_end_at(self) -> None:
        task = _make_task()
        task.start()
        task.complete()
        assert task.actual_end_at is not None

    def test_complete_from_created_raises(self) -> None:
        task = _make_task()
        with pytest.raises(InvalidFieldError):
            task.complete()

    def test_complete_from_stopped_raises(self) -> None:
        task = _make_task()
        task.start()
        task.stop()
        with pytest.raises(InvalidFieldError):
            task.complete()


# ---------------------------------------------------------------------------
# ProductionTask — close
# ---------------------------------------------------------------------------


class TestProductionTaskClose:
    def test_close_sets_closed(self) -> None:
        task = _make_task()
        task.start()
        task.complete()
        task.close()
        assert task.status == TaskStatus.closed

    def test_close_from_created_raises(self) -> None:
        task = _make_task()
        with pytest.raises(InvalidFieldError):
            task.close()

    def test_close_from_in_progress_raises(self) -> None:
        task = _make_task()
        task.start()
        with pytest.raises(InvalidFieldError):
            task.close()

    def test_close_from_stopped_raises(self) -> None:
        task = _make_task()
        task.start()
        task.stop()
        with pytest.raises(InvalidFieldError):
            task.close()

    def test_close_from_closed_raises(self) -> None:
        task = _make_task()
        task.start()
        task.complete()
        task.close()
        with pytest.raises(InvalidFieldError):
            task.close()


# ---------------------------------------------------------------------------
# ProductionTask — delete (soft)
# ---------------------------------------------------------------------------


class TestProductionTaskDelete:
    def test_delete_sets_inactive(self) -> None:
        task = _make_task()
        task.delete()
        assert task.is_active is False

    def test_delete_from_in_progress(self) -> None:
        task = _make_task()
        task.start()
        task.delete()
        assert task.is_active is False

    def test_delete_from_stopped(self) -> None:
        task = _make_task()
        task.start()
        task.stop()
        task.delete()
        assert task.is_active is False

    def test_delete_closed_raises(self) -> None:
        task = _make_task()
        task.start()
        task.complete()
        task.close()
        with pytest.raises(InvalidFieldError):
            task.delete()

    def test_delete_already_deleted_raises(self) -> None:
        task = _make_task()
        task.delete()
        with pytest.raises(InvalidFieldError):
            task.delete()


# ---------------------------------------------------------------------------
# Simple entities
# ---------------------------------------------------------------------------


class TestTaskStop:
    def test_construction(self) -> None:
        ts = TaskStop(task_id=1, reason="broken machine", stopped_at=datetime.now(timezone.utc))
        assert ts.task_id == 1
        assert ts.reason == "broken machine"
        assert ts.resumed_at is None


class TestTaskCompletion:
    def test_construction(self) -> None:
        tc = TaskCompletion(task_id=1, actual_quantity=200)
        assert tc.task_id == 1
        assert tc.actual_quantity == 200
        assert tc.comment is None


class TestTaskCompletionConsumption:
    def test_construction(self) -> None:
        tcc = TaskCompletionConsumption(
            completion_id=1,
            raw_material_id=2,
            planned_qty=Decimal("55.0"),
            actual_qty=Decimal("53.5"),
        )
        assert tcc.completion_id == 1
        assert tcc.waste_qty is None


class TestRawMaterialReservation:
    def test_construction(self) -> None:
        r = RawMaterialReservation(stock_id=1, task_id=2, quantity=Decimal("10.5"))
        assert r.stock_id == 1
        assert r.quantity == Decimal("10.5")
        assert r.id is None


# ---------------------------------------------------------------------------
# Domain service — calculate_material_requirements
# ---------------------------------------------------------------------------


class _FakeRecipeLine:
    def __init__(self, raw_material_id: int, consumption_per_unit: Decimal, waste_percentage: Decimal) -> None:
        self.raw_material_id = raw_material_id
        self.consumption_per_unit = consumption_per_unit
        self.waste_percentage = waste_percentage


class TestCalculateMaterialRequirements:
    def test_single_material_no_waste(self) -> None:
        lines = [_FakeRecipeLine(1, Decimal("0.5"), Decimal("0"))]
        result = calculate_material_requirements(100, lines)
        assert len(result) == 1
        rm_id, qty = result[0]
        assert rm_id == 1
        assert qty == Decimal("50.0")

    def test_single_material_with_waste(self) -> None:
        lines = [_FakeRecipeLine(1, Decimal("0.5"), Decimal("10"))]
        result = calculate_material_requirements(100, lines)
        rm_id, qty = result[0]
        assert rm_id == 1
        assert qty == Decimal("55.0")

    def test_multiple_materials(self) -> None:
        lines = [
            _FakeRecipeLine(1, Decimal("0.5"), Decimal("0")),
            _FakeRecipeLine(2, Decimal("0.2"), Decimal("5")),
        ]
        result = calculate_material_requirements(100, lines)
        assert len(result) == 2
        ids = {r[0] for r in result}
        assert {1, 2} == ids

    def test_empty_recipe(self) -> None:
        result = calculate_material_requirements(100, [])
        assert result == []

    def test_zero_waste_percentage(self) -> None:
        lines = [_FakeRecipeLine(1, Decimal("1.0"), Decimal("0"))]
        result = calculate_material_requirements(10, lines)
        assert result[0][1] == Decimal("10.0")
