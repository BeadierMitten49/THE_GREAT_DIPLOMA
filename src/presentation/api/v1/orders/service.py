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
    get_order_reservations,
    get_orders,
    release_order_reservations,
    release_product_reservation,
    reserve_product_for_order,
)
from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.value_objects import OrderStatus
from src.infrastructure.db.repositories.auth import UserRepository
from src.infrastructure.db.repositories.orders import (
    OrderItemRepository,
    OrderRepository,
    ProductReservationRepository,
)
from src.infrastructure.db.repositories.references import CustomerRepository, ProductRepository
from src.infrastructure.db.repositories.tasks import ProductionTaskRepository
from src.infrastructure.db.repositories.warehouse import ProductStockRepository


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._order_repo = OrderRepository(session)
        self._item_repo = OrderItemRepository(session)
        self._reservation_repo = ProductReservationRepository(session)
        self._stock_repo = ProductStockRepository(session)
        self._customer_repo = CustomerRepository(session)
        self._user_repo = UserRepository(session)
        self._product_repo = ProductRepository(session)
        self._task_repo = ProductionTaskRepository(session)

    async def get(self, order_id: int) -> Order:
        return await get_order(order_id, self._order_repo)

    async def get_all(
        self,
        status: OrderStatus | None = None,
        customer_id: int | None = None,
        delivery_date_from: date | None = None,
        delivery_date_to: date | None = None,
    ) -> list[Order]:
        return await get_orders(
            self._order_repo,
            status=status,
            customer_id=customer_id,
            delivery_date_from=delivery_date_from,
            delivery_date_to=delivery_date_to,
        )

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
            dto, self._order_repo, self._item_repo, self._reservation_repo, self._stock_repo,
            task_repo=self._task_repo,
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

    async def get_reservations(self, order_id: int) -> list[ProductReservation]:
        return await get_order_reservations(order_id, self._order_repo, self._reservation_repo)

    async def reserve(self, order_id: int, stock_id: int, quantity: int) -> int:
        return await reserve_product_for_order(
            order_id, stock_id, quantity,
            self._order_repo, self._reservation_repo, self._stock_repo,
        )

    async def release_reservation(self, reservation_id: int) -> None:
        await release_product_reservation(reservation_id, self._reservation_repo)

    async def release_all_reservations(self, order_id: int) -> None:
        await release_order_reservations(order_id, self._order_repo, self._reservation_repo)

    async def get_product_info(self, product_id: int) -> tuple[str, int]:
        product = await self._product_repo.get_by_id(product_id)
        if product:
            return product.name, product.units_per_box
        return f"Продукт #{product_id}", 1

    async def get_customer_name(self, customer_id: int) -> str:
        customer = await self._customer_repo.get_by_id(customer_id)
        return customer.name if customer else f"Клиент #{customer_id}"

    async def get_delivery_user_name(self, user_id: int) -> str | None:
        user = await self._user_repo.get_by_id(user_id)
        return user.full_name if user else None

    async def get_drawer_data(self, order_id: int) -> dict:
        order = await self.get(order_id)
        items = await self.get_items(order_id)
        reservations = await self.get_reservations(order_id)

        reservations_by_item: dict[int, list[dict]] = {}
        for r in reservations:
            stock = await self._stock_repo.get_by_id(r.stock_id)
            batch_label = f"П-{stock.batch_year}-{stock.batch_number:03d}" if stock else "?"
            product_id_for_stock = stock.product_id if stock else 0
            reservations_by_item.setdefault(product_id_for_stock, []).append({
                "reservation_id": r.id,
                "stock_id": r.stock_id,
                "batch_label": batch_label,
                "quantity": r.quantity,
            })

        tasks_raw = await self._task_repo.get_by_order(order_id)
        tasks = []
        for t in tasks_raw:
            product_name, _ = await self.get_product_info(t.product_id)
            executor = await self._user_repo.get_by_id(t.executor_id)
            tasks.append({
                "task_id": t.id,
                "product_name": product_name,
                "quantity": t.quantity,
                "executor_name": executor.full_name if executor else f"#{t.executor_id}",
                "deadline": t.deadline,
                "status": t.status,
            })

        return {
            "order": order,
            "items": items,
            "reservations_by_item": reservations_by_item,
            "tasks": tasks,
        }
