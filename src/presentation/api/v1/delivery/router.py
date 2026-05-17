from fastapi import APIRouter, Depends, status

from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.domain.delivery.value_objects import DeliveryStatus
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.dependencies import director_only, director_or_delivery
from src.presentation.api.v1.delivery.dependencies import get_delivery_service
from src.presentation.api.v1.delivery.schemas import (
    CancelDeliveryRequest,
    CreateDeliveryRequest,
    DeliveryResponse,
)
from src.presentation.api.v1.delivery.service import DeliveryService

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


def _delivery_response(delivery) -> DeliveryResponse:
    return DeliveryResponse(
        id=delivery.id,
        order_id=delivery.order_id,
        executor_id=delivery.executor_id,
        status=delivery.status,
        planned_date=delivery.planned_date,
        started_at=delivery.started_at,
        completed_at=delivery.completed_at,
        cancellation_reason=delivery.cancellation_reason,
    )


@router.get("", response_model=list[DeliveryResponse], dependencies=[director_or_delivery])
async def get_deliveries(
    status: DeliveryStatus | None = None,
    executor_id: int | None = None,
    current_user: User = Depends(get_current_user),
    service: DeliveryService = Depends(get_delivery_service),
):
    if current_user.has_role(Role.delivery) and not current_user.has_role(Role.director):
        executor_id = current_user.id
    deliveries = await service.get_all(executor_id=executor_id, status=status)
    return [_delivery_response(d) for d in deliveries]


@router.get("/{id}", response_model=DeliveryResponse, dependencies=[director_or_delivery])
async def get_delivery(
    id: int,
    service: DeliveryService = Depends(get_delivery_service),
):
    return _delivery_response(await service.get(id))


@router.post(
    "",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[director_only],
)
async def create_delivery(
    body: CreateDeliveryRequest,
    service: DeliveryService = Depends(get_delivery_service),
):
    delivery_id = await service.create(
        order_id=body.order_id,
        executor_id=body.executor_id,
        planned_date=body.planned_date,
    )
    return _delivery_response(await service.get(delivery_id))


@router.post("/{id}/pick-up", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_or_delivery])
async def pick_up_order(id: int, service: DeliveryService = Depends(get_delivery_service)):
    await service.pick_up(id)


@router.post("/{id}/start", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_or_delivery])
async def start_delivery(id: int, service: DeliveryService = Depends(get_delivery_service)):
    await service.start(id)


@router.post("/{id}/complete", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_or_delivery])
async def complete_delivery(id: int, service: DeliveryService = Depends(get_delivery_service)):
    await service.complete(id)


@router.post("/{id}/cancel", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_or_delivery])
async def cancel_delivery(
    id: int,
    body: CancelDeliveryRequest,
    service: DeliveryService = Depends(get_delivery_service),
):
    await service.cancel(id, body.reason)
