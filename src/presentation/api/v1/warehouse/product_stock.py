from fastapi import APIRouter, Depends, status

from src.presentation.api.v1.dependencies import director_only, director_or_warehouse
from src.presentation.api.v1.warehouse.dependencies import get_product_stock_service
from src.presentation.api.v1.warehouse.schemas import (
    ProductStockAdjustRequest,
    ProductStockArrivalRequest,
    ProductStockResponse,
    ProductStockWriteOffRequest,
)
from src.presentation.api.v1.warehouse.service import ProductStockService

router = APIRouter(
    prefix="/product-stock",
    tags=["Product Stock"],
    dependencies=[director_or_warehouse],
)


async def _to_response(entity, service: ProductStockService) -> ProductStockResponse:
    reserved, reserved_orders = await service.get_reserved(entity.id)
    return ProductStockResponse(
        id=entity.id,
        product_id=entity.product_id,
        quantity=entity.quantity,
        reserved=reserved,
        reserved_orders=reserved_orders,
        batch_number=entity.batch_number,
        batch_year=entity.batch_year,
        arrival_date=entity.arrival_date,
        expiry_date=entity.expiry_date,
        comment=entity.comment,
    )


@router.get("", response_model=list[ProductStockResponse])
async def get_product_stocks(
    product_id: int | None = None,
    service: ProductStockService = Depends(get_product_stock_service),
):
    if product_id is not None:
        entities = await service.get_by_product(product_id)
    else:
        entities = await service.get_all()
    return [await _to_response(s, service) for s in entities]


@router.get("/{id}", response_model=ProductStockResponse)
async def get_product_stock(
    id: int,
    service: ProductStockService = Depends(get_product_stock_service),
):
    return await _to_response(await service.get(id), service)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def product_stock_arrival(
    body: ProductStockArrivalRequest,
    service: ProductStockService = Depends(get_product_stock_service),
):
    id = await service.arrival(
        body.product_id, body.quantity, body.arrival_date, body.expiry_date, body.comment
    )
    return {"id": id}


@router.patch("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def product_stock_adjust(
    id: int,
    body: ProductStockAdjustRequest,
    service: ProductStockService = Depends(get_product_stock_service),
):
    await service.adjust(id, body.quantity, body.comment)


@router.post("/{id}/write-off", status_code=status.HTTP_204_NO_CONTENT, dependencies=[director_only])
async def product_stock_write_off(
    id: int,
    body: ProductStockWriteOffRequest,
    service: ProductStockService = Depends(get_product_stock_service),
):
    await service.write_off(id, body.amount)
