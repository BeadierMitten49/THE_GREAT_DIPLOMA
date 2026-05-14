from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.session import get_session
from src.presentation.api.v1.references.service import (
    CustomerService,
    PackagingService,
    ProductService,
    RawMaterialService,
)


def get_customer_service(session: AsyncSession = Depends(get_session)) -> CustomerService:
    return CustomerService(session)


def get_product_service(session: AsyncSession = Depends(get_session)) -> ProductService:
    return ProductService(session)


def get_raw_material_service(session: AsyncSession = Depends(get_session)) -> RawMaterialService:
    return RawMaterialService(session)


def get_packaging_service(session: AsyncSession = Depends(get_session)) -> PackagingService:
    return PackagingService(session)
