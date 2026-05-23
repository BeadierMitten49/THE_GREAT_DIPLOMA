from datetime import date

from fastapi import APIRouter, Depends, status

from src.domain.orders.value_objects import OrderStatus
from src.presentation.api.v1.dependencies import director_only, director_or_warehouse_or_delivery
from src.presentation.api.v1.orders.dependencies import get_order_service
from src.presentation.api.v1.orders.schemas import (
    ChangeOrderStatusRequest,
    CreateOrderRequest,
    EditOrderRequest,
    ItemReservationInfo,
    OrderDrawerResponse,
    OrderItemResponse,
    OrderResponse,
    OrderTaskInfo,
    ProductReservationResponse,
    ReserveProductRequest,
)
from src.presentation.api.v1.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"], dependencies=[director_only])


async def _to_response(order, service: OrderService) -> OrderResponse:
    customer_name = await service.get_customer_name(order.customer_id)
    delivery_user_name = None
    if order.delivery_user_id:
        delivery_user_name = await service.get_delivery_user_name(order.delivery_user_id)
    return OrderResponse(
        id=order.id,
        number=order.number,
        customer_id=order.customer_id,
        customer_name=customer_name,
        delivery_address=order.delivery_address,
        delivery_date=order.delivery_date,
        status=order.status,
        delivery_user_id=order.delivery_user_id,
        delivery_user_name=delivery_user_name,
        comment=order.comment,
        created_at=order.created_at,
    )


async def _item_response(item, service: OrderService) -> OrderItemResponse:
    product_name, units_per_box = await service.get_product_info(item.product_id)
    return OrderItemResponse(
        id=item.id,
        order_id=item.order_id,
        product_id=item.product_id,
        product_name=product_name,
        units_per_box=units_per_box,
        quantity=item.quantity,
    )


@router.get("", response_model=list[OrderResponse])
async def get_orders(
    status: OrderStatus | None = None,
    customer_id: int | None = None,
    delivery_date_from: date | None = None,
    delivery_date_to: date | None = None,
    service: OrderService = Depends(get_order_service),
):
    orders = await service.get_all(
        status=status,
        customer_id=customer_id,
        delivery_date_from=delivery_date_from,
        delivery_date_to=delivery_date_to,
    )
    return [await _to_response(o, service) for o in orders]


@router.get("/{id}", response_model=OrderResponse)
async def get_order(id: int, service: OrderService = Depends(get_order_service)):
    return await _to_response(await service.get(id), service)


@router.get("/{id}/items", response_model=list[OrderItemResponse])
async def get_order_items(id: int, service: OrderService = Depends(get_order_service)):
    items = await service.get_items(id)
    return [await _item_response(i, service) for i in items]


@router.get("/{id}/drawer", response_model=OrderDrawerResponse)
async def get_order_drawer(id: int, service: OrderService = Depends(get_order_service)):
    data = await service.get_drawer_data(id)
    order_resp = await _to_response(data["order"], service)
    items_resp = [await _item_response(i, service) for i in data["items"]]
    reservations_resp = {
        str(pid): [ItemReservationInfo(**r) for r in rs]
        for pid, rs in data["reservations_by_item"].items()
    }
    tasks_resp = [OrderTaskInfo(**t) for t in data["tasks"]]
    return OrderDrawerResponse(
        order=order_resp,
        items=items_resp,
        reservations_by_item=reservations_resp,
        tasks=tasks_resp,
    )


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


@router.get("/{id}/reservations", response_model=list[ProductReservationResponse])
async def get_order_reservations(id: int, service: OrderService = Depends(get_order_service)):
    reservations = await service.get_reservations(id)
    return [
        ProductReservationResponse(id=r.id, order_id=r.order_id, stock_id=r.stock_id, quantity=r.quantity)
        for r in reservations
    ]


@router.post("/{id}/reservations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def reserve_product(
    id: int,
    body: ReserveProductRequest,
    service: OrderService = Depends(get_order_service),
):
    reservation_id = await service.reserve(id, body.stock_id, body.quantity)
    return {"id": reservation_id}


@router.delete("/reservation/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def release_reservation(
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
