from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.orders.dto import ChangeOrderStatusDTO, CreateOrderDTO, EditOrderDTO
from src.application.orders.use_cases import (
    change_order_status,
    create_order,
    delete_order,
    edit_order,
    get_order,
    get_order_items,
    get_orders,
    release_order_reservations,
    release_product_reservation,
    reserve_product_for_order,
)
from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.value_objects import OrderStatus
from src.infrastructure.db.repositories.orders import (
    OrderItemRepository,
    OrderRepository,
    ProductReservationRepository,
)
from src.infrastructure.db.repositories.warehouse import ProductStockRepository


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._order_repo = OrderRepository(session)
        self._item_repo = OrderItemRepository(session)
        self._reservation_repo = ProductReservationRepository(session)
        self._stock_repo = ProductStockRepository(session)

    async def get(self, order_id: int) -> Order:
        return await get_order(order_id, self._order_repo)

    async def get_all(
        self,
        status: OrderStatus | None = None,
        customer_id: int | None = None,
    ) -> list[Order]:
        return await get_orders(self._order_repo, status=status, customer_id=customer_id)

    async def get_items(self, order_id: int) -> list[OrderItem]:
        return await get_order_items(order_id, self._item_repo)

    async def create(
        self,
        customer_id: int,
        delivery_address: str,
        delivery_date: date,
        items: list[tuple[int, int]],
        delivery_user_id: int | None,
        comment: str | None,
    ) -> int:
        dto = CreateOrderDTO(
            customer_id=customer_id,
            delivery_address=delivery_address,
            delivery_date=delivery_date,
            items=items,
            delivery_user_id=delivery_user_id,
            comment=comment,
        )
        return await create_order(dto, self._order_repo, self._item_repo)

    async def change_status(self, order_id: int, new_status: OrderStatus) -> None:
        dto = ChangeOrderStatusDTO(order_id=order_id, new_status=new_status)
        await change_order_status(
            dto, self._order_repo, self._item_repo, self._reservation_repo, self._stock_repo
        )

    async def edit(
        self,
        order_id: int,
        delivery_address: str,
        delivery_date: date,
        items: list[tuple[int, int]],
        delivery_user_id: int | None,
        comment: str | None,
    ) -> None:
        dto = EditOrderDTO(
            order_id=order_id,
            delivery_address=delivery_address,
            delivery_date=delivery_date,
            items=items,
            delivery_user_id=delivery_user_id,
            comment=comment,
        )
        await edit_order(dto, self._order_repo, self._item_repo)

    async def delete(self, order_id: int) -> None:
        await delete_order(order_id, self._order_repo, self._reservation_repo)

    async def reserve(self, order_id: int, stock_id: int, quantity: int) -> int:
        return await reserve_product_for_order(
            order_id, stock_id, quantity,
            self._order_repo, self._reservation_repo, self._stock_repo,
        )

    async def release_reservation(self, reservation_id: int) -> None:
        await release_product_reservation(reservation_id, self._reservation_repo)

    async def release_all_reservations(self, order_id: int) -> None:
        await release_order_reservations(order_id, self._order_repo, self._reservation_repo)
