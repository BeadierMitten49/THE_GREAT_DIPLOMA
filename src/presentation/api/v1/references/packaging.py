from fastapi import APIRouter, Depends, status

from src.presentation.api.v1.dependencies import authenticated, director_only
from src.presentation.api.v1.references.dependencies import get_packaging_service
from src.presentation.api.v1.references.schemas import (
    CreatePackagingRequest,
    PackagingResponse,
    UpdatePackagingRequest,
)
from src.presentation.api.v1.references.service import PackagingService

router = APIRouter(prefix="/packaging", tags=["Packaging"], dependencies=[authenticated])


def _to_response(entity) -> PackagingResponse:
    return PackagingResponse(
        id=entity.id,
        name=entity.name,
        unit=entity.unit,
        critical_stock=entity.critical_stock,
        is_active=entity.is_active,
        comment=entity.comment,
    )


@router.get("", response_model=list[PackagingResponse])
async def get_packagings(
    include_inactive: bool = False,
    service: PackagingService = Depends(get_packaging_service),
):
    return [_to_response(p) for p in await service.get_all(include_inactive)]


@router.get("/{id}", response_model=PackagingResponse)
async def get_packaging(id: int, service: PackagingService = Depends(get_packaging_service)):
    return _to_response(await service.get(id))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[director_only])
async def create_packaging(
    body: CreatePackagingRequest,
    service: PackagingService = Depends(get_packaging_service),
):
    id = await service.create(body.name, body.unit, body.critical_stock, body.comment)
    return {"id": id}


@router.patch("/{id}", response_model=PackagingResponse, dependencies=[director_only])
async def update_packaging(
    id: int,
    body: UpdatePackagingRequest,
    service: PackagingService = Depends(get_packaging_service),
):
    await service.update(id, body.name, body.unit, body.critical_stock, body.comment)
    return _to_response(await service.get(id))


@router.post("/{id}/deactivate", status_code=status.HTTP_204_NO_CONTENT, dependencies=[director_only])
async def deactivate_packaging(id: int, service: PackagingService = Depends(get_packaging_service)):
    await service.deactivate(id)


@router.post("/{id}/activate", status_code=status.HTTP_204_NO_CONTENT, dependencies=[director_only])
async def activate_packaging(id: int, service: PackagingService = Depends(get_packaging_service)):
    await service.activate(id)
