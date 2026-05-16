from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from src.domain.references.entities import Product, RecipeLine
from src.domain.tasks.entities import (
    ProductionTask,
    RawMaterialReservation,
    TaskCompletion,
    TaskCompletionConsumption,
    TaskStop,
)
from src.domain.tasks.value_objects import TaskStatus, TaskType
from src.domain.warehouse.entities import RawMaterialStock


# ---------------------------------------------------------------------------
# Fake repositories
# ---------------------------------------------------------------------------


class FakeProductionTaskRepository:
    def __init__(self) -> None:
        self._store: dict[int, ProductionTask] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> ProductionTask | None:
        return self._store.get(id)

    async def save(self, entity: ProductionTask) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_all(self, include_inactive: bool = False) -> list[ProductionTask]:
        tasks = list(self._store.values())
        if not include_inactive:
            tasks = [t for t in tasks if t.is_active]
        return tasks

    async def get_by_status(self, status: TaskStatus) -> list[ProductionTask]:
        return [t for t in self._store.values() if t.status == status and t.is_active]

    async def get_by_executor(self, executor_id: int) -> list[ProductionTask]:
        return [t for t in self._store.values() if t.executor_id == executor_id and t.is_active]

    async def get_by_order(self, order_id: int) -> list[ProductionTask]:
        return [t for t in self._store.values() if t.order_id == order_id and t.is_active]


class FakeTaskStopRepository:
    def __init__(self) -> None:
        self._store: dict[int, TaskStop] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> TaskStop | None:
        return self._store.get(id)

    async def save(self, entity: TaskStop) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_all(self) -> list[TaskStop]:
        return list(self._store.values())

    async def get_by_task(self, task_id: int) -> list[TaskStop]:
        return [s for s in self._store.values() if s.task_id == task_id]

    async def get_open_stop(self, task_id: int) -> TaskStop | None:
        for s in self._store.values():
            if s.task_id == task_id and s.resumed_at is None:
                return s
        return None


class FakeTaskCompletionRepository:
    def __init__(self) -> None:
        self._store: dict[int, TaskCompletion] = {}
        self._consumptions: dict[int, list[TaskCompletionConsumption]] = {}
        self._next_id = 1
        self._next_consumption_id = 1

    async def get_by_id(self, id: int) -> TaskCompletion | None:
        return self._store.get(id)

    async def save(self, entity: TaskCompletion) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_all(self) -> list[TaskCompletion]:
        return list(self._store.values())

    async def get_by_task(self, task_id: int) -> TaskCompletion | None:
        for c in self._store.values():
            if c.task_id == task_id:
                return c
        return None

    async def get_consumptions(self, completion_id: int) -> list[TaskCompletionConsumption]:
        return self._consumptions.get(completion_id, [])

    async def save_consumption(self, consumption: TaskCompletionConsumption) -> int:
        if consumption.id is None:
            consumption.id = self._next_consumption_id
            self._next_consumption_id += 1
        self._consumptions.setdefault(consumption.completion_id, []).append(consumption)
        return consumption.id


class FakeRawMaterialReservationRepository:
    def __init__(self) -> None:
        self._store: dict[int, RawMaterialReservation] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> RawMaterialReservation | None:
        return self._store.get(id)

    async def save(self, entity: RawMaterialReservation) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_all(self) -> list[RawMaterialReservation]:
        return list(self._store.values())

    async def get_by_task(self, task_id: int) -> list[RawMaterialReservation]:
        return [r for r in self._store.values() if r.task_id == task_id]

    async def get_by_stock(self, stock_id: int) -> list[RawMaterialReservation]:
        return [r for r in self._store.values() if r.stock_id == stock_id]

    async def delete_by_task(self, task_id: int) -> None:
        self._store = {rid: r for rid, r in self._store.items() if r.task_id != task_id}


class FakeRawMaterialStockRepository:
    def __init__(self, batches: list[RawMaterialStock] | None = None) -> None:
        self._store: dict[int, RawMaterialStock] = {}
        self._next_id = 1
        for b in (batches or []):
            b.id = self._next_id
            self._store[self._next_id] = b
            self._next_id += 1

    async def get_by_id(self, id: int) -> RawMaterialStock | None:
        return self._store.get(id)

    async def save(self, entity: RawMaterialStock) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_all(self) -> list[RawMaterialStock]:
        return list(self._store.values())

    async def get_by_raw_material(self, raw_material_id: int) -> list[RawMaterialStock]:
        return [b for b in self._store.values() if b.raw_material_id == raw_material_id]


class FakeProductRepository:
    def __init__(self, product: Product) -> None:
        self._product = product

    async def get_by_id(self, id: int) -> Product | None:
        if self._product.id == id:
            return self._product
        return None

    async def save(self, entity: Product) -> int: ...
    async def get_all(self, include_inactive: bool = False) -> list[Product]: ...
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_recipe_line(rm_id: int, consumption: str = "0.5", waste: str = "10") -> RecipeLine:
    return RecipeLine(
        raw_material_id=rm_id,
        consumption_per_unit=Decimal(consumption),
        waste_percentage=Decimal(waste),
    )


def _make_product(recipe_lines: list[RecipeLine] | None = None) -> Product:
    p = Product(
        id=1,
        name="Juice",
        units_per_box=12,
        shelf_life_days=180,
        critical_stock=100,
    )
    p.recipe = recipe_lines if recipe_lines is not None else [_make_recipe_line(rm_id=1)]
    return p


def _make_stock(rm_id: int, qty: str, stock_id: int | None = None) -> RawMaterialStock:
    s = RawMaterialStock(
        raw_material_id=rm_id,
        quantity=Decimal(qty),
        arrival_date=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
        id=stock_id,
    )
    return s


def _make_task(status: TaskStatus = TaskStatus.created) -> ProductionTask:
    task = ProductionTask(
        product_id=1,
        quantity=100,
        executor_id=2,
        start_date=date(2026, 6, 1),
        deadline=date(2026, 6, 10),
        task_type=TaskType.stock_task,
        id=1,
        status=status,
    )
    return task


@pytest.fixture
def task_repo() -> FakeProductionTaskRepository:
    return FakeProductionTaskRepository()


@pytest.fixture
def stop_repo() -> FakeTaskStopRepository:
    return FakeTaskStopRepository()


@pytest.fixture
def completion_repo() -> FakeTaskCompletionRepository:
    return FakeTaskCompletionRepository()


@pytest.fixture
def reservation_repo() -> FakeRawMaterialReservationRepository:
    return FakeRawMaterialReservationRepository()


@pytest.fixture
def stock_repo() -> FakeRawMaterialStockRepository:
    # 100 units of rm_id=1 available
    # quantity=100, consumption=0.5, waste=10% → needed = 100*0.5*1.1 = 55 < 100 → sufficient
    return FakeRawMaterialStockRepository(
        batches=[_make_stock(rm_id=1, qty="100")]
    )


@pytest.fixture
def product_repo() -> FakeProductRepository:
    return FakeProductRepository(_make_product())


@pytest.fixture
async def saved_task(task_repo: FakeProductionTaskRepository) -> ProductionTask:
    task = _make_task()
    task.id = None
    await task_repo.save(task)
    return task
