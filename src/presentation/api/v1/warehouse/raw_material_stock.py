from decimal import Decimal

from fastapi import APIRouter, Depends, status

from src.presentation.api.v1.dependencies import director_or_warehouse
from src.presentation.api.v1.warehouse.dependencies import get_raw_material_stock_service
from src.presentation.api.v1.warehouse.schemas import (
    RawMaterialStockAdjustRequest,
    RawMaterialStockArrivalRequest,
    RawMaterialStockResponse,
    RawMaterialStockWriteOffRequest,
)
from src.presentation.api.v1.warehouse.service import RawMaterialStockService

router = APIRouter(
    prefix="/raw-material-stock",
    tags=["Raw Material Stock"],
    dependencies=[director_or_warehouse],
)


async def _to_response(entity, service: RawMaterialStockService) -> RawMaterialStockResponse:
    reserved = await service.get_reserved(entity.id)
    return RawMaterialStockResponse(
        id=entity.id,
        raw_material_id=entity.raw_material_id,
        quantity=entity.quantity,
        reserved=reserved,
        arrival_date=entity.arrival_date,
        expiry_date=entity.expiry_date,
        comment=entity.comment,
    )


@router.get("", response_model=list[RawMaterialStockResponse])
async def get_raw_material_stocks(
    raw_material_id: int | None = None,
    service: RawMaterialStockService = Depends(get_raw_material_stock_service),
):
    stocks = await service.get_by_material(raw_material_id) if raw_material_id is not None else await service.get_all()
    return [await _to_response(s, service) for s in stocks]


@router.get("/{id}", response_model=RawMaterialStockResponse)
async def get_raw_material_stock(
    id: int,
    service: RawMaterialStockService = Depends(get_raw_material_stock_service),
):
    return await _to_response(await service.get(id), service)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def raw_material_stock_arrival(
    body: RawMaterialStockArrivalRequest,
    service: RawMaterialStockService = Depends(get_raw_material_stock_service),
):
    id = await service.arrival(
        body.raw_material_id, body.quantity, body.arrival_date, body.expiry_date, body.comment
    )
    return {"id": id}


@router.post("/{id}/write-off", status_code=status.HTTP_204_NO_CONTENT)
async def raw_material_stock_write_off(
    id: int,
    body: RawMaterialStockWriteOffRequest,
    service: RawMaterialStockService = Depends(get_raw_material_stock_service),
):
    await service.write_off(id, body.amount)


@router.patch("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def raw_material_stock_adjust(
    id: int,
    body: RawMaterialStockAdjustRequest,
    service: RawMaterialStockService = Depends(get_raw_material_stock_service),
):
    await service.adjust(id, body.quantity, body.comment)
