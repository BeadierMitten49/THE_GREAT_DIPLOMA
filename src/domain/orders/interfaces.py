from abc import abstractmethod

from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.value_objects import OrderStatus
from src.domain.shared.repository import IPlainRepository, ISoftDeleteRepository


class IOrderRepository(ISoftDeleteRepository[Order]):
    @abstractmethod
    async def get_by_status(self, status: OrderStatus) -> list[Order]: ...

    @abstractmethod
    async def get_by_customer(self, customer_id: int) -> list[Order]: ...

    @abstractmethod
    async def get_last_order_number(self) -> int: ...


class IOrderItemRepository(IPlainRepository[OrderItem]):
    @abstractmethod
    async def get_by_order(self, order_id: int) -> list[OrderItem]: ...

    @abstractmethod
    async def delete_by_order(self, order_id: int) -> None: ...


class IProductReservationRepository(IPlainRepository[ProductReservation]):
    @abstractmethod
    async def get_by_order(self, order_id: int) -> list[ProductReservation]: ...

    @abstractmethod
    async def get_by_stock(self, stock_id: int) -> list[ProductReservation]: ...

    @abstractmethod
    async def delete_by_order(self, order_id: int) -> None: ...

    @abstractmethod
    async def delete_by_id(self, reservation_id: int) -> None: ...
