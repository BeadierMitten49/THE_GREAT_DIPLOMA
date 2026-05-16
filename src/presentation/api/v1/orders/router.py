from fastapi import APIRouter, Depends, status

from src.domain.orders.value_objects import OrderStatus
from src.presentation.api.v1.dependencies import director_only, director_or_warehouse_or_delivery
from src.presentation.api.v1.orders.dependencies import get_order_service
from src.presentation.api.v1.orders.schemas import (
    ChangeOrderStatusRequest,
    CreateOrderRequest,
    EditOrderRequest,
    OrderItemResponse,
    OrderResponse,
    ProductReservationResponse,
    ReserveProductRequest,
)
from src.presentation.api.v1.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"], dependencies=[director_only])


def _order_response(order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        number=order.number,
        customer_id=order.customer_id,
        delivery_address=order.delivery_address,
        delivery_date=order.delivery_date,
        status=order.status,
        delivery_user_id=order.delivery_user_id,
        comment=order.comment,
        created_at=order.created_at,
    )


def _item_response(item) -> OrderItemResponse:
    return OrderItemResponse(
        id=item.id,
        order_id=item.order_id,
        product_id=item.product_id,
        quantity=item.quantity,
    )


@router.get("", response_model=list[OrderResponse])
async def get_orders(
    status: OrderStatus | None = None,
    customer_id: int | None = None,
    service: OrderService = Depends(get_order_service),
):
    orders = await service.get_all(status=status, customer_id=customer_id)
    return [_order_response(o) for o in orders]


@router.get("/{id}", response_model=OrderResponse)
async def get_order(id: int, service: OrderService = Depends(get_order_service)):
    return _order_response(await service.get(id))


@router.get("/{id}/items", response_model=list[OrderItemResponse])
async def get_order_items(id: int, service: OrderService = Depends(get_order_service)):
    items = await service.get_items(id)
    return [_item_response(i) for i in items]


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
):
    id_ = await service.create(
        customer_id=body.customer_id,
        delivery_address=body.delivery_address,
        delivery_date=body.delivery_date,
        items=[(i.product_id, i.quantity) for i in body.items],
        delivery_user_id=body.delivery_user_id,
        comment=body.comment,
    )
    return {"id": id_}


@router.patch(
    "/{id}/status",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[director_or_warehouse_or_delivery],
)
async def change_order_status(
    id: int,
    body: ChangeOrderStatusRequest,
    service: OrderService = Depends(get_order_service),
):
    await service.change_status(id, body.new_status)


@router.put("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def edit_order(
    id: int,
    body: EditOrderRequest,
    service: OrderService = Depends(get_order_service),
):
    await service.edit(
        order_id=id,
        delivery_address=body.delivery_address,
        delivery_date=body.delivery_date,
        items=[(i.product_id, i.quantity) for i in body.items],
        delivery_user_id=body.delivery_user_id,
        comment=body.comment,
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(id: int, service: OrderService = Depends(get_order_service)):
    await service.delete(id)


@router.post("/{id}/reservations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def reserve_product(
    id: int,
    body: ReserveProductRequest,
    service: OrderService = Depends(get_order_service),
):
    reservation_id = await service.reserve(id, body.stock_id, body.quantity)
    return {"id": reservation_id}


@router.delete("/{id}/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def release_reservation(
    id: int,
    reservation_id: int,
    service: OrderService = Depends(get_order_service),
):
    await service.release_reservation(reservation_id)


@router.delete("/{id}/reservations", status_code=status.HTTP_204_NO_CONTENT)
async def release_all_reservations(
    id: int,
    service: OrderService = Depends(get_order_service),
):
    await service.release_all_reservations(id)
