from fastapi import APIRouter, Depends, status

from src.presentation.api.v1.dependencies import director_only
from src.presentation.api.v1.references.dependencies import get_product_service
from src.presentation.api.v1.references.schemas import (
    CreateProductRequest,
    ProductResponse,
    RecipeLineResponse,
    SetRecipeRequest,
    UpdateProductRequest,
)
from src.presentation.api.v1.references.service import ProductService

router = APIRouter(prefix="/products", tags=["Products"], dependencies=[director_only])


def _to_response(entity) -> ProductResponse:
    return ProductResponse(
        id=entity.id,
        name=entity.name,
        units_per_box=entity.units_per_box,
        shelf_life_days=entity.shelf_life_days,
        critical_stock=entity.critical_stock,
        is_active=entity.is_active,
        recipe=[
            RecipeLineResponse(
                id=line.id,
                raw_material_id=line.raw_material_id,
                consumption_per_unit=line.consumption_per_unit,
                waste_percentage=line.waste_percentage,
            )
            for line in entity.recipe
        ],
    )


@router.get("", response_model=list[ProductResponse])
async def get_products(
    include_inactive: bool = False,
    service: ProductService = Depends(get_product_service),
):
    return [_to_response(p) for p in await service.get_all(include_inactive)]


@router.get("/{id}", response_model=ProductResponse)
async def get_product(id: int, service: ProductService = Depends(get_product_service)):
    return _to_response(await service.get(id))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: CreateProductRequest,
    service: ProductService = Depends(get_product_service),
):
    id = await service.create(body.name, body.units_per_box, body.shelf_life_days, body.critical_stock)
    return {"id": id}


@router.patch("/{id}", response_model=ProductResponse)
async def update_product(
    id: int,
    body: UpdateProductRequest,
    service: ProductService = Depends(get_product_service),
):
    await service.update(id, body.name, body.units_per_box, body.shelf_life_days, body.critical_stock)
    return _to_response(await service.get(id))


@router.put("/{id}/recipe", status_code=status.HTTP_204_NO_CONTENT)
async def set_recipe(
    id: int,
    body: SetRecipeRequest,
    service: ProductService = Depends(get_product_service),
):
    lines = [(l.raw_material_id, l.consumption_per_unit, l.waste_percentage) for l in body.lines]
    await service.set_recipe(id, lines)


@router.post("/{id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_product(id: int, service: ProductService = Depends(get_product_service)):
    await service.deactivate(id)


@router.post("/{id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_product(id: int, service: ProductService = Depends(get_product_service)):
    await service.activate(id)
