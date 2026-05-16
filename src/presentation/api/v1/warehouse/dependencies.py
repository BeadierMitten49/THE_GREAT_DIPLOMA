from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.session import get_session
from src.presentation.api.v1.warehouse.service import (
    PackagingStockService,
    ProductStockService,
    RawMaterialStockService,
)


def get_raw_material_stock_service(
    session: AsyncSession = Depends(get_session),
) -> RawMaterialStockService:
    return RawMaterialStockService(session)


def get_packaging_stock_service(
    session: AsyncSession = Depends(get_session),
) -> PackagingStockService:
    return PackagingStockService(session)


def get_product_stock_service(
    session: AsyncSession = Depends(get_session),
) -> ProductStockService:
    return ProductStockService(session)
