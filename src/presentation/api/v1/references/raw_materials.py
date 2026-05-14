from fastapi import APIRouter, Depends, status

from src.presentation.api.v1.dependencies import director_only
from src.presentation.api.v1.references.dependencies import get_raw_material_service
from src.presentation.api.v1.references.schemas import (
    CreateRawMaterialRequest,
    RawMaterialResponse,
    UpdateRawMaterialRequest,
)
from src.presentation.api.v1.references.service import RawMaterialService

router = APIRouter(prefix="/raw-materials", tags=["Raw Materials"], dependencies=[director_only])


def _to_response(entity) -> RawMaterialResponse:
    return RawMaterialResponse(
        id=entity.id,
        name=entity.name,
        unit=entity.unit,
        shelf_life_days=entity.shelf_life_days,
        critical_stock=entity.critical_stock,
        is_active=entity.is_active,
    )


@router.get("", response_model=list[RawMaterialResponse])
async def get_raw_materials(
    include_inactive: bool = False,
    service: RawMaterialService = Depends(get_raw_material_service),
):
    return [_to_response(r) for r in await service.get_all(include_inactive)]


@router.get("/{id}", response_model=RawMaterialResponse)
async def get_raw_material(id: int, service: RawMaterialService = Depends(get_raw_material_service)):
    return _to_response(await service.get(id))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_raw_material(
    body: CreateRawMaterialRequest,
    service: RawMaterialService = Depends(get_raw_material_service),
):
    id = await service.create(body.name, body.unit, body.shelf_life_days, body.critical_stock)
    return {"id": id}


@router.patch("/{id}", response_model=RawMaterialResponse)
async def update_raw_material(
    id: int,
    body: UpdateRawMaterialRequest,
    service: RawMaterialService = Depends(get_raw_material_service),
):
    await service.update(id, body.name, body.unit, body.shelf_life_days, body.critical_stock)
    return _to_response(await service.get(id))


@router.post("/{id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_raw_material(id: int, service: RawMaterialService = Depends(get_raw_material_service)):
    await service.deactivate(id)


@router.post("/{id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_raw_material(id: int, service: RawMaterialService = Depends(get_raw_material_service)):
    await service.activate(id)
