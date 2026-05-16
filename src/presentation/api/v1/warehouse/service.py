from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.warehouse.dto import (
    PackagingStockArrivalDTO,
    PackagingStockWriteOffDTO,
    ProductStockArrivalDTO,
    ProductStockWriteOffDTO,
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
    product_stock_arrival,
    product_stock_write_off,
    raw_material_stock_arrival,
    raw_material_stock_write_off,
)
from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock
from src.infrastructure.db.repositories.warehouse import (
    PackagingStockRepository,
    ProductStockRepository,
    RawMaterialStockRepository,
)


class RawMaterialStockService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = RawMaterialStockRepository(session)

    async def get(self, id: int) -> RawMaterialStock:
        return await get_raw_material_stock(id, self._repo)

    async def get_all(self) -> list[RawMaterialStock]:
        return await get_raw_material_stocks(self._repo)

    async def get_by_material(self, raw_material_id: int) -> list[RawMaterialStock]:
        return await get_raw_material_stocks_by_material(raw_material_id, self._repo)

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

    async def get(self, id: int) -> ProductStock:
        return await get_product_stock(id, self._repo)

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

    async def write_off(self, stock_id: int, amount: int) -> None:
        await product_stock_write_off(ProductStockWriteOffDTO(stock_id, amount), self._repo)
