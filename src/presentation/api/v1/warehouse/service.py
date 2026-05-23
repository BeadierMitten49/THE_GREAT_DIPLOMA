from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.warehouse.dto import (
    PackagingStockArrivalDTO,
    PackagingStockWriteOffDTO,
    ProductStockAdjustDTO,
    ProductStockArrivalDTO,
    ProductStockWriteOffDTO,
    RawMaterialStockAdjustDTO,
    RawMaterialStockArrivalDTO,
    RawMaterialStockWriteOffDTO,
)
from src.application.warehouse.use_cases import (
    get_packaging_stock,
    get_packaging_stocks,
    get_packaging_stocks_by_packaging,
    get_product_stock,
    get_product_stocks,
    get_product_stocks_by_product,
    get_raw_material_stock,
    get_raw_material_stocks,
    get_raw_material_stocks_by_material,
    packaging_stock_arrival,
    packaging_stock_write_off,
    product_stock_adjust,
    product_stock_arrival,
    product_stock_write_off,
    raw_material_stock_adjust,
    raw_material_stock_arrival,
    raw_material_stock_write_off,
)
from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock
from src.application.shared.exceptions import NotFoundError
from src.application.tasks.use_cases import close_task
from src.domain.shared.exceptions import InvalidFieldError
from src.domain.tasks.value_objects import TaskStatus
from src.infrastructure.db.repositories.orders import ProductReservationRepository
from src.infrastructure.db.repositories.references import ProductRepository
from src.infrastructure.db.repositories.tasks import (
    ProductionTaskRepository,
    RawMaterialReservationRepository,
    TaskCompletionRepository,
)
from src.infrastructure.db.repositories.warehouse import (
    PackagingStockRepository,
    ProductStockRepository,
    RawMaterialStockRepository,
)


class RawMaterialStockService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = RawMaterialStockRepository(session)
        self._reservation_repo = RawMaterialReservationRepository(session)

    async def get(self, id: int) -> RawMaterialStock:
        return await get_raw_material_stock(id, self._repo)

    async def get_all(self) -> list[RawMaterialStock]:
        return await get_raw_material_stocks(self._repo)

    async def get_by_material(self, raw_material_id: int) -> list[RawMaterialStock]:
        return await get_raw_material_stocks_by_material(raw_material_id, self._repo)

    async def get_reserved(self, stock_id: int) -> Decimal:
        reservations = await self._reservation_repo.get_by_stock(stock_id)
        return sum((r.quantity for r in reservations), Decimal("0"))

    async def arrival(
        self,
        raw_material_id: int,
        quantity: Decimal,
        arrival_date: date,
        expiry_date: date,
        comment: str | None,
    ) -> int:
        return await raw_material_stock_arrival(
            RawMaterialStockArrivalDTO(raw_material_id, quantity, arrival_date, expiry_date, comment),
            self._repo,
        )

    async def write_off(self, stock_id: int, amount: Decimal) -> None:
        await raw_material_stock_write_off(RawMaterialStockWriteOffDTO(stock_id, amount), self._repo)

    async def adjust(self, stock_id: int, quantity: Decimal, comment: str | None) -> None:
        await raw_material_stock_adjust(RawMaterialStockAdjustDTO(stock_id, quantity, comment), self._repo)


class PackagingStockService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = PackagingStockRepository(session)

    async def get(self, id: int) -> PackagingStock:
        return await get_packaging_stock(id, self._repo)

    async def get_all(self) -> list[PackagingStock]:
        return await get_packaging_stocks(self._repo)

    async def get_by_packaging(self, packaging_id: int) -> list[PackagingStock]:
        return await get_packaging_stocks_by_packaging(packaging_id, self._repo)

    async def arrival(self, packaging_id: int, quantity: int, comment: str | None) -> int:
        return await packaging_stock_arrival(
            PackagingStockArrivalDTO(packaging_id, quantity, comment), self._repo
        )

    async def write_off(self, stock_id: int, amount: int) -> None:
        await packaging_stock_write_off(PackagingStockWriteOffDTO(stock_id, amount), self._repo)


class ProductStockService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProductStockRepository(session)
        self._reservation_repo = ProductReservationRepository(session)
        self._task_repo = ProductionTaskRepository(session)
        self._completion_repo = TaskCompletionRepository(session)
        self._product_repo = ProductRepository(session)

    async def get(self, id: int) -> ProductStock:
        return await get_product_stock(id, self._repo)

    async def get_reserved(self, stock_id: int) -> tuple[int, list[int]]:
        reservations = await self._reservation_repo.get_by_stock(stock_id)
        total = sum(r.quantity for r in reservations)
        order_ids = sorted(set(r.order_id for r in reservations))
        return total, order_ids

    async def get_all(self) -> list[ProductStock]:
        return await get_product_stocks(self._repo)

    async def get_by_product(self, product_id: int) -> list[ProductStock]:
        return await get_product_stocks_by_product(product_id, self._repo)

    async def arrival(
        self,
        product_id: int,
        quantity: int,
        arrival_date: date,
        expiry_date: date,
        comment: str | None,
    ) -> int:
        return await product_stock_arrival(
            ProductStockArrivalDTO(product_id, quantity, arrival_date, expiry_date, comment),
            self._repo,
        )

    async def adjust(self, stock_id: int, quantity: int, comment: str | None) -> None:
        await product_stock_adjust(ProductStockAdjustDTO(stock_id, quantity, comment), self._repo)

    async def get_pending_acceptances(self) -> list[dict]:
        tasks = await self._task_repo.get_by_status(TaskStatus.completed)
        result = []
        for task in tasks:
            completion = await self._completion_repo.get_by_task(task.id)
            product = await self._product_repo.get_by_id(task.product_id)
            result.append({
                "task_id": task.id,
                "product_id": task.product_id,
                "product_name": product.name if product else "?",
                "planned_quantity": task.quantity,
                "actual_quantity": completion.actual_quantity if completion else 0,
                "completed_at": task.actual_end_at.isoformat() if task.actual_end_at else None,
            })
        return result

    async def accept_from_task(self, task_id: int) -> int:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise NotFoundError("ProductionTask", task_id)
        if task.status != TaskStatus.completed:
            raise InvalidFieldError("status", "task must be in 'completed' status")

        completion = await self._completion_repo.get_by_task(task_id)
        if completion is None:
            raise NotFoundError("TaskCompletion", task_id)

        product = await self._product_repo.get_by_id(task.product_id)
        if product is None:
            raise NotFoundError("Product", task.product_id)

        today = date.today()
        expiry = today + timedelta(days=product.shelf_life_days)
        stock_id = await self.arrival(
            task.product_id,
            completion.actual_quantity,
            today,
            expiry,
            f"Приёмка по задаче #{task_id}",
        )

        await close_task(task_id, self._task_repo)
        return stock_id

    async def write_off(self, stock_id: int, amount: int) -> None:
        await product_stock_write_off(ProductStockWriteOffDTO(stock_id, amount), self._repo)
