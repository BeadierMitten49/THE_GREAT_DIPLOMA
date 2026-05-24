from sqlalchemy import delete, func, select

from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.interfaces import (
    IOrderItemRepository,
    IOrderRepository,
    IProductReservationRepository,
)
from src.domain.orders.value_objects import OrderStatus
from src.infrastructure.db.models.orders import OrderItemModel, OrderModel, ProductReservationModel
from src.infrastructure.db.repositories.base import BasePlainRepository, BaseSoftDeleteRepository


class OrderRepository(BaseSoftDeleteRepository[Order, OrderModel], IOrderRepository):
    @property
    def _model_class(self) -> type[OrderModel]:
        return OrderModel

    def _to_entity(self, model: OrderModel) -> Order:
        return Order(
            id=model.id,
            number=model.number,
            customer_id=model.customer_id,
            delivery_address=model.delivery_address,
            delivery_date=model.delivery_date,
            status=OrderStatus(model.status),
            delivery_user_id=model.delivery_user_id,
            comment=model.comment,
            is_active=model.is_active,
            created_at=model.created_at,
        )

    def _to_values(self, entity: Order) -> dict:
        return {
            "number": entity.number,
            "customer_id": entity.customer_id,
            "delivery_address": entity.delivery_address,
            "delivery_date": entity.delivery_date,
            "status": entity.status,
            "delivery_user_id": entity.delivery_user_id,
            "comment": entity.comment,
            "is_active": entity.is_active,
        }

    async def get_by_status(self, status: OrderStatus) -> list[Order]:
        stmt = select(OrderModel).where(
            OrderModel.status == status,
            OrderModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_customer(self, customer_id: int) -> list[Order]:
        stmt = select(OrderModel).where(
            OrderModel.customer_id == customer_id,
            OrderModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_last_order_number(self) -> int:
        stmt = select(func.max(OrderModel.number))
        result = await self._session.execute(stmt)
        return result.scalar() or 0


class OrderItemRepository(
    BasePlainRepository[OrderItem, OrderItemModel],
    IOrderItemRepository,
):
    @property
    def _model_class(self) -> type[OrderItemModel]:
        return OrderItemModel

    def _to_entity(self, model: OrderItemModel) -> OrderItem:
        return OrderItem(
            id=model.id,
            order_id=model.order_id,
            product_id=model.product_id,
            quantity=model.quantity,
            is_assembled=model.is_assembled,
        )

    def _to_values(self, entity: OrderItem) -> dict:
        return {
            "order_id": entity.order_id,
            "product_id": entity.product_id,
            "quantity": entity.quantity,
            "is_assembled": entity.is_assembled,
        }

    async def get_by_order(self, order_id: int) -> list[OrderItem]:
        stmt = select(OrderItemModel).where(OrderItemModel.order_id == order_id)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def delete_by_order(self, order_id: int) -> None:
        await self._session.execute(
            delete(OrderItemModel).where(OrderItemModel.order_id == order_id)
        )


class ProductReservationRepository(
    BasePlainRepository[ProductReservation, ProductReservationModel],
    IProductReservationRepository,
):
    @property
    def _model_class(self) -> type[ProductReservationModel]:
        return ProductReservationModel

    def _to_entity(self, model: ProductReservationModel) -> ProductReservation:
        return ProductReservation(
            id=model.id,
            order_id=model.order_id,
            stock_id=model.stock_id,
            quantity=model.quantity,
        )

    def _to_values(self, entity: ProductReservation) -> dict:
        return {
            "order_id": entity.order_id,
            "stock_id": entity.stock_id,
            "quantity": entity.quantity,
        }

    async def get_by_order(self, order_id: int) -> list[ProductReservation]:
        stmt = select(ProductReservationModel).where(
            ProductReservationModel.order_id == order_id
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_stock(self, stock_id: int) -> list[ProductReservation]:
        stmt = select(ProductReservationModel).where(
            ProductReservationModel.stock_id == stock_id
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def delete_by_order(self, order_id: int) -> None:
        await self._session.execute(
            delete(ProductReservationModel).where(
                ProductReservationModel.order_id == order_id
            )
        )

    async def delete_by_id(self, reservation_id: int) -> None:
        await self._session.execute(
            delete(ProductReservationModel).where(
                ProductReservationModel.id == reservation_id
            )
        )
