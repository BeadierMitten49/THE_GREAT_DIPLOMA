from datetime import date, datetime, timezone
from decimal import Decimal

from src.application.shared.exceptions import NotFoundError
from src.application.tasks.dto import CompleteTaskDTO, CreateTaskDTO
from src.domain.orders.entities import ProductReservation
from src.domain.orders.interfaces import IProductReservationRepository
from src.domain.shared.exceptions import InvalidFieldError
from src.domain.tasks.entities import (
    ProductionTask,
    RawMaterialReservation,
    TaskCompletion,
    TaskCompletionConsumption,
    TaskStop,
    calculate_material_requirements,
)
from src.domain.tasks.interfaces import (
    IProductionTaskRepository,
    IRawMaterialReservationRepository,
    ITaskCompletionRepository,
    ITaskStopRepository,
)
from src.domain.tasks.value_objects import TaskStatus, TaskType
from src.domain.warehouse.entities import ProductStock
from src.domain.warehouse.interfaces import IProductStockRepository, IRawMaterialStockRepository
from src.domain.references.interfaces import IProductRepository


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


async def get_task(task_id: int, repo: IProductionTaskRepository) -> ProductionTask:
    task = await repo.get_by_id(task_id)
    if task is None:
        raise NotFoundError("ProductionTask", task_id)
    return task


async def get_tasks(
    repo: IProductionTaskRepository,
    status: TaskStatus | None = None,
    executor_id: int | None = None,
) -> list[ProductionTask]:
    if status is not None:
        return await repo.get_by_status(status)
    if executor_id is not None:
        return await repo.get_by_executor(executor_id)
    return await repo.get_all()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_task(
    dto: CreateTaskDTO,
    task_repo: IProductionTaskRepository,
    product_repo: IProductRepository,
    stock_repo: IRawMaterialStockRepository,
    reservation_repo: IRawMaterialReservationRepository,
) -> tuple[int, list[int]]:
    """Create task, auto-allocate raw material reservations FIFO by expiry date.

    Returns (task_id, insufficient_material_ids) — task is always created even if stock
    is insufficient; insufficient_material_ids lists raw_material_ids where stock fell short.
    """
    task = ProductionTask(
        product_id=dto.product_id,
        quantity=dto.quantity,
        executor_id=dto.executor_id,
        start_date=dto.start_date,
        deadline=dto.deadline,
        task_type=dto.task_type,
        order_id=dto.order_id,
        comment=dto.comment,
    )
    await task_repo.save(task)

    product = await product_repo.get_by_id(dto.product_id)
    if product is None:
        raise NotFoundError("Product", dto.product_id)

    requirements = calculate_material_requirements(dto.quantity, product.recipe)
    insufficient: list[int] = []

    for rm_id, needed in requirements:
        batches = await stock_repo.get_by_raw_material(rm_id)
        batches.sort(key=lambda b: b.expiry_date)
        remaining = needed

        for batch in batches:
            if remaining <= 0:
                break
            existing = await reservation_repo.get_by_stock(batch.id)
            already_reserved = sum(r.quantity for r in existing)
            available = batch.quantity - already_reserved
            if available <= 0:
                continue
            allocate = min(available, remaining)
            await reservation_repo.save(
                RawMaterialReservation(stock_id=batch.id, task_id=task.id, quantity=allocate)
            )
            remaining -= allocate

        if remaining > 0:
            insufficient.append(rm_id)

    return task.id, insufficient


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


async def start_task(task_id: int, task_repo: IProductionTaskRepository) -> None:
    task = await get_task(task_id, task_repo)
    task.start()
    await task_repo.save(task)


async def stop_task(
    task_id: int,
    reason: str,
    task_repo: IProductionTaskRepository,
    stop_repo: ITaskStopRepository,
) -> None:
    task = await get_task(task_id, task_repo)
    task.stop()
    await task_repo.save(task)
    await stop_repo.save(
        TaskStop(task_id=task_id, reason=reason, stopped_at=datetime.now(timezone.utc))
    )


async def resume_task(
    task_id: int,
    task_repo: IProductionTaskRepository,
    stop_repo: ITaskStopRepository,
) -> None:
    task = await get_task(task_id, task_repo)
    task.resume()
    await task_repo.save(task)
    open_stop = await stop_repo.get_open_stop(task_id)
    if open_stop is not None:
        open_stop.resumed_at = datetime.now(timezone.utc)
        await stop_repo.save(open_stop)


async def complete_task(
    dto: CompleteTaskDTO,
    task_repo: IProductionTaskRepository,
    product_repo: IProductRepository,
    completion_repo: ITaskCompletionRepository,
) -> None:
    task = await get_task(dto.task_id, task_repo)
    task.complete()
    await task_repo.save(task)

    completion = TaskCompletion(
        task_id=dto.task_id,
        actual_quantity=dto.actual_quantity,
        comment=dto.comment,
    )
    await completion_repo.save(completion)

    product = await product_repo.get_by_id(task.product_id)
    planned_map: dict[int, Decimal] = {}
    if product is not None:
        planned_map = {
            rm_id: qty
            for rm_id, qty in calculate_material_requirements(task.quantity, product.recipe)
        }

    for item in dto.consumptions:
        await completion_repo.save_consumption(
            TaskCompletionConsumption(
                completion_id=completion.id,
                raw_material_id=item.raw_material_id,
                planned_qty=planned_map.get(item.raw_material_id, Decimal("0")),
                actual_qty=item.actual_qty,
                waste_qty=item.waste_qty,
            )
        )


async def close_task(
    task_id: int,
    task_repo: IProductionTaskRepository,
    completion_repo: ITaskCompletionRepository,
    product_stock_repo: IProductStockRepository,
    raw_material_stock_repo: IRawMaterialStockRepository,
    raw_material_reservation_repo: IRawMaterialReservationRepository | None = None,
    product_reservation_repo: IProductReservationRepository | None = None,
) -> None:
    task = await get_task(task_id, task_repo)
    task.close()
    await task_repo.save(task)

    # ── Снятие резервов сырья ──
    if raw_material_reservation_repo is not None:
        await raw_material_reservation_repo.delete_by_task(task_id)

    # ── Списание сырья по фактическому расходу ──
    completion = await completion_repo.get_by_task(task_id)
    if completion is not None:
        consumptions = await completion_repo.get_consumptions(completion.id)
        for cons in consumptions:
            if cons.actual_qty <= 0:
                continue
            batches = await raw_material_stock_repo.get_by_raw_material(cons.raw_material_id)
            batches.sort(key=lambda b: b.expiry_date)
            remaining = cons.actual_qty
            for batch in batches:
                if remaining <= 0:
                    break
                can_take = min(batch.quantity, remaining)
                if can_take <= 0:
                    continue
                batch.write_off(can_take)
                if batch.quantity == 0:
                    await raw_material_stock_repo.delete(batch.id)
                else:
                    await raw_material_stock_repo.save(batch)
                remaining -= can_take

    # ── Добавление продукции на склад ──
    quantity = completion.actual_quantity if completion else task.quantity
    today = date.today()
    last_batch = await product_stock_repo.get_last_batch_number(today.year)
    comment = f"Произведено по задаче #{task_id}"
    if task.order_id is not None:
        comment += f" для заказа #{task.order_id}"
    stock = ProductStock(
        product_id=task.product_id,
        quantity=quantity,
        batch_number=last_batch + 1,
        batch_year=today.year,
        arrival_date=today,
        expiry_date=date(today.year, 12, 31),
        comment=comment,
    )
    await product_stock_repo.save(stock)

    # ── Резерв продукции под заказ (только order_task) ──
    if (
        task.task_type == TaskType.order_task
        and task.order_id is not None
        and product_reservation_repo is not None
    ):
        await product_reservation_repo.save(
            ProductReservation(order_id=task.order_id, stock_id=stock.id, quantity=quantity)
        )


# ---------------------------------------------------------------------------
# Management
# ---------------------------------------------------------------------------


async def reassign_task(
    task_id: int,
    new_executor_id: int,
    task_repo: IProductionTaskRepository,
) -> None:
    task = await get_task(task_id, task_repo)
    if task.status == TaskStatus.closed:
        raise InvalidFieldError("status", "cannot reassign closed task")
    task.executor_id = new_executor_id
    await task_repo.save(task)


async def delete_task(
    task_id: int,
    task_repo: IProductionTaskRepository,
    reservation_repo: IRawMaterialReservationRepository,
) -> None:
    task = await get_task(task_id, task_repo)
    await reservation_repo.delete_by_task(task_id)
    task.delete()
    await task_repo.save(task)
