from fastapi import APIRouter, Depends, status

from src.presentation.api.v1.references.dependencies import get_customer_service
from src.presentation.api.v1.references.schemas import (
    CreateCustomerRequest,
    CustomerResponse,
    UpdateCustomerRequest,
)
from src.presentation.api.v1.references.service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


def _to_response(entity) -> CustomerResponse:
    return CustomerResponse(
        id=entity.id,
        name=entity.name,
        default_address=entity.default_address,
        is_active=entity.is_active,
    )


@router.get("", response_model=list[CustomerResponse])
async def get_customers(
    include_inactive: bool = False,
    service: CustomerService = Depends(get_customer_service),
):
    return [_to_response(c) for c in await service.get_all(include_inactive)]


@router.get("/{id}", response_model=CustomerResponse)
async def get_customer(id: int, service: CustomerService = Depends(get_customer_service)):
    return _to_response(await service.get(id))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CreateCustomerRequest,
    service: CustomerService = Depends(get_customer_service),
):
    id = await service.create(body.name, body.default_address)
    return {"id": id}


@router.patch("/{id}", response_model=CustomerResponse)
async def update_customer(
    id: int,
    body: UpdateCustomerRequest,
    service: CustomerService = Depends(get_customer_service),
):
    await service.update(id, body.name, body.default_address)
    return _to_response(await service.get(id))


@router.post("/{id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_customer(id: int, service: CustomerService = Depends(get_customer_service)):
    await service.deactivate(id)


@router.post("/{id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_customer(id: int, service: CustomerService = Depends(get_customer_service)):
    await service.activate(id)
