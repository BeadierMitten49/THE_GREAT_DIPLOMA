from fastapi import APIRouter, Depends, status

from src.presentation.api.v1.dependencies import director_or_warehouse
from src.presentation.api.v1.warehouse.dependencies import get_packaging_stock_service
from src.presentation.api.v1.warehouse.schemas import (
    PackagingStockArrivalRequest,
    PackagingStockResponse,
    PackagingStockWriteOffRequest,
)
from src.presentation.api.v1.warehouse.service import PackagingStockService

router = APIRouter(
    prefix="/packaging-stock",
    tags=["Packaging Stock"],
    dependencies=[director_or_warehouse],
)


def _to_response(entity) -> PackagingStockResponse:
    return PackagingStockResponse(
        id=entity.id,
        packaging_id=entity.packaging_id,
        quantity=entity.quantity,
        comment=entity.comment,
    )


@router.get("", response_model=list[PackagingStockResponse])
async def get_packaging_stocks(
    packaging_id: int | None = None,
    service: PackagingStockService = Depends(get_packaging_stock_service),
):
    if packaging_id is not None:
        return [_to_response(s) for s in await service.get_by_packaging(packaging_id)]
    return [_to_response(s) for s in await service.get_all()]


@router.get("/{id}", response_model=PackagingStockResponse)
async def get_packaging_stock(
    id: int,
    service: PackagingStockService = Depends(get_packaging_stock_service),
):
    return _to_response(await service.get(id))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def packaging_stock_arrival(
    body: PackagingStockArrivalRequest,
    service: PackagingStockService = Depends(get_packaging_stock_service),
):
    id = await service.arrival(body.packaging_id, body.quantity, body.comment)
    return {"id": id}


@router.post("/{id}/write-off", status_code=status.HTTP_204_NO_CONTENT)
async def packaging_stock_write_off(
    id: int,
    body: PackagingStockWriteOffRequest,
    service: PackagingStockService = Depends(get_packaging_stock_service),
):
    await service.write_off(id, body.amount)
