from src.application.warehouse.dto import (
    PackagingStockArrivalDTO,
    PackagingStockWriteOffDTO,
    ProductStockArrivalDTO,
    RawMaterialStockArrivalDTO,
    RawMaterialStockWriteOffDTO,
)
from src.application.warehouse.exceptions import NotFoundError
from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock
from src.domain.warehouse.interfaces import (
    IPackagingStockRepository,
    IProductStockRepository,
    IRawMaterialStockRepository,
)


# ---------------------------------------------------------------------------
# RawMaterialStock
# ---------------------------------------------------------------------------


async def get_raw_material_stock(id: int, repo: IRawMaterialStockRepository) -> RawMaterialStock:
    stock = await repo.get_by_id(id)
    if stock is None:
        raise NotFoundError("RawMaterialStock", id)
    return stock


async def get_raw_material_stocks(repo: IRawMaterialStockRepository) -> list[RawMaterialStock]:
    return await repo.get_all()


async def get_raw_material_stocks_by_material(
    raw_material_id: int, repo: IRawMaterialStockRepository
) -> list[RawMaterialStock]:
    return await repo.get_by_raw_material(raw_material_id)


async def raw_material_stock_arrival(
    dto: RawMaterialStockArrivalDTO, repo: IRawMaterialStockRepository
) -> int:
    stock = RawMaterialStock(
        raw_material_id=dto.raw_material_id,
        quantity=dto.quantity,
        arrival_date=dto.arrival_date,
        expiry_date=dto.expiry_date,
        comment=dto.comment,
    )
    return await repo.save(stock)


async def raw_material_stock_write_off(
    dto: RawMaterialStockWriteOffDTO, repo: IRawMaterialStockRepository
) -> None:
    stock = await repo.get_by_id(dto.stock_id)
    if stock is None:
        raise NotFoundError("RawMaterialStock", dto.stock_id)
    stock.write_off(dto.amount)
    await repo.save(stock)


# ---------------------------------------------------------------------------
# PackagingStock
# ---------------------------------------------------------------------------


async def get_packaging_stock(id: int, repo: IPackagingStockRepository) -> PackagingStock:
    stock = await repo.get_by_id(id)
    if stock is None:
        raise NotFoundError("PackagingStock", id)
    return stock


async def get_packaging_stocks(repo: IPackagingStockRepository) -> list[PackagingStock]:
    return await repo.get_all()


async def get_packaging_stocks_by_packaging(
    packaging_id: int, repo: IPackagingStockRepository
) -> list[PackagingStock]:
    return await repo.get_by_packaging(packaging_id)


async def packaging_stock_arrival(
    dto: PackagingStockArrivalDTO, repo: IPackagingStockRepository
) -> int:
    stock = PackagingStock(
        packaging_id=dto.packaging_id,
        quantity=dto.quantity,
        comment=dto.comment,
    )
    return await repo.save(stock)


async def packaging_stock_write_off(
    dto: PackagingStockWriteOffDTO, repo: IPackagingStockRepository
) -> None:
    stock = await repo.get_by_id(dto.stock_id)
    if stock is None:
        raise NotFoundError("PackagingStock", dto.stock_id)
    stock.write_off(dto.amount)
    await repo.save(stock)


# ---------------------------------------------------------------------------
# ProductStock
# ---------------------------------------------------------------------------


async def get_product_stock(id: int, repo: IProductStockRepository) -> ProductStock:
    stock = await repo.get_by_id(id)
    if stock is None:
        raise NotFoundError("ProductStock", id)
    return stock


async def get_product_stocks(repo: IProductStockRepository) -> list[ProductStock]:
    return await repo.get_all()


async def get_product_stocks_by_product(
    product_id: int, repo: IProductStockRepository
) -> list[ProductStock]:
    return await repo.get_by_product(product_id)


async def product_stock_arrival(
    dto: ProductStockArrivalDTO, repo: IProductStockRepository
) -> int:
    last_batch = await repo.get_last_batch_number(dto.arrival_date.year)
    stock = ProductStock(
        product_id=dto.product_id,
        quantity=dto.quantity,
        batch_number=last_batch + 1,
        batch_year=dto.arrival_date.year,
        arrival_date=dto.arrival_date,
        expiry_date=dto.expiry_date,
        comment=dto.comment,
    )
    return await repo.save(stock)
