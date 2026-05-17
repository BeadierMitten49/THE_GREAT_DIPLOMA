from src.application.orders.dto import ChangeOrderStatusDTO, CreateOrderDTO, EditOrderDTO
from src.application.orders.exceptions import InsufficientStockError, NotFoundError
from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.interfaces import (
    IOrderItemRepository,
    IOrderRepository,
    IProductReservationRepository,
)
from src.domain.orders.value_objects import OrderStatus
from src.domain.shared.exceptions import InvalidFieldError
from src.domain.warehouse.interfaces import IProductStockRepository

_NOT_EDITABLE = {OrderStatus.delivery, OrderStatus.completed}


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


async def get_order(order_id: int, repo: IOrderRepository) -> Order:
    order = await repo.get_by_id(order_id)
    if order is None:
        raise NotFoundError("Order", order_id)
    return order


async def get_orders(
    repo: IOrderRepository,
    status: OrderStatus | None = None,
    customer_id: int | None = None,
) -> list[Order]:
    if status is not None:
        return await repo.get_by_status(status)
    if customer_id is not None:
        return await repo.get_by_customer(customer_id)
    return await repo.get_all()


async def get_order_items(
    order_id: int, item_repo: IOrderItemRepository
) -> list[OrderItem]:
    return await item_repo.get_by_order(order_id)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_order(
    dto: CreateOrderDTO,
    order_repo: IOrderRepository,
    item_repo: IOrderItemRepository,
) -> int:
    last_number = await order_repo.get_last_order_number()
    order = Order(
        customer_id=dto.customer_id,
        delivery_address=dto.delivery_address,
        delivery_date=dto.delivery_date,
        delivery_user_id=dto.delivery_user_id,
        comment=dto.comment,
        number=last_number + 1,
    )
    await order_repo.save(order)

    for product_id, quantity in dto.items:
        await item_repo.save(OrderItem(order_id=order.id, product_id=product_id, quantity=quantity))

    return order.id


# ---------------------------------------------------------------------------
# Change status
# ---------------------------------------------------------------------------


async def change_order_status(
    dto: ChangeOrderStatusDTO,
    order_repo: IOrderRepository,
    item_repo: IOrderItemRepository,
    reservation_repo: IProductReservationRepository,
    stock_repo: IProductStockRepository,
) -> None:
    order = await order_repo.get_by_id(dto.order_id)
    if order is None:
        raise NotFoundError("Order", dto.order_id)

    if dto.new_status == OrderStatus.assembly:
        await _validate_reservations_cover_items(
            order.id, item_repo, reservation_repo, stock_repo
        )

    if dto.new_status == OrderStatus.delivery:
        await _ship_stock(order.id, reservation_repo, stock_repo)

    order.change_status(dto.new_status)
    await order_repo.save(order)


async def _validate_reservations_cover_items(
    order_id: int,
    item_repo: IOrderItemRepository,
    reservation_repo: IProductReservationRepository,
    stock_repo: IProductStockRepository,
) -> None:
    items = await item_repo.get_by_order(order_id)
    reservations = await reservation_repo.get_by_order(order_id)

    reserved_by_product: dict[int, int] = {}
    for res in reservations:
        stock = await stock_repo.get_by_id(res.stock_id)
        if stock is not None:
            reserved_by_product[stock.product_id] = (
                reserved_by_product.get(stock.product_id, 0) + res.quantity
            )

    for item in items:
        covered = reserved_by_product.get(item.product_id, 0)
        if covered < item.quantity:
            raise InsufficientStockError(item.product_id, item.quantity, covered)


async def _ship_stock(
    order_id: int,
    reservation_repo: IProductReservationRepository,
    stock_repo: IProductStockRepository,
) -> None:
    reservations = await reservation_repo.get_by_order(order_id)
    for res in reservations:
        stock = await stock_repo.get_by_id(res.stock_id)
        if stock is not None:
            stock.write_off(res.quantity)
            await stock_repo.save(stock)
    await reservation_repo.delete_by_order(order_id)


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------


async def edit_order(
    dto: EditOrderDTO,
    order_repo: IOrderRepository,
    item_repo: IOrderItemRepository,
) -> None:
    order = await order_repo.get_by_id(dto.order_id)
    if order is None:
        raise NotFoundError("Order", dto.order_id)
    if order.status in _NOT_EDITABLE:
        raise InvalidFieldError("status", f"cannot edit order in status '{order.status}'")

    order.delivery_address = dto.delivery_address
    order.delivery_date = dto.delivery_date
    order.delivery_user_id = dto.delivery_user_id
    order.comment = dto.comment
    await order_repo.save(order)

    await item_repo.delete_by_order(order.id)
    for product_id, quantity in dto.items:
        await item_repo.save(OrderItem(order_id=order.id, product_id=product_id, quantity=quantity))


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


async def delete_order(
    order_id: int,
    order_repo: IOrderRepository,
    reservation_repo: IProductReservationRepository,
) -> None:
    order = await order_repo.get_by_id(order_id)
    if order is None:
        raise NotFoundError("Order", order_id)
    await reservation_repo.delete_by_order(order_id)
    order.delete()
    await order_repo.save(order)


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------


async def reserve_product_for_order(
    order_id: int,
    stock_id: int,
    quantity: int,
    order_repo: IOrderRepository,
    reservation_repo: IProductReservationRepository,
    stock_repo: IProductStockRepository,
) -> int:
    order = await order_repo.get_by_id(order_id)
    if order is None:
        raise NotFoundError("Order", order_id)

    stock = await stock_repo.get_by_id(stock_id)
    if stock is None:
        raise NotFoundError("ProductStock", stock_id)

    existing = await reservation_repo.get_by_stock(stock_id)
    already_reserved = sum(r.quantity for r in existing)
    available = stock.quantity - already_reserved
    if quantity > available:
        raise InsufficientStockError(stock.product_id, quantity, available)

    reservation = ProductReservation(order_id=order_id, stock_id=stock_id, quantity=quantity)
    return await reservation_repo.save(reservation)


async def release_product_reservation(
    order_id: int,
    reservation_id: int,
    reservation_repo: IProductReservationRepository,
) -> None:
    reservation = await reservation_repo.get_by_id(reservation_id)
    if reservation is None:
        raise NotFoundError("ProductReservation", reservation_id)
    if reservation.order_id != order_id:
        raise NotFoundError("ProductReservation", reservation_id)
    await reservation_repo.delete_by_id(reservation_id)


async def release_order_reservations(
    order_id: int,
    order_repo: IOrderRepository,
    reservation_repo: IProductReservationRepository,
) -> None:
    order = await order_repo.get_by_id(order_id)
    if order is None:
        raise NotFoundError("Order", order_id)
    await reservation_repo.delete_by_order(order_id)
