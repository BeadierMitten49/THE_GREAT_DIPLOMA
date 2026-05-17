from abc import abstractmethod

from src.domain.delivery.entities import Delivery
from src.domain.delivery.value_objects import DeliveryStatus
from src.domain.shared.repository import IPlainRepository


class IDeliveryRepository(IPlainRepository[Delivery]):
    @abstractmethod
    async def get_by_order(self, order_id: int) -> Delivery | None: ...

    @abstractmethod
    async def get_by_executor(self, executor_id: int) -> list[Delivery]: ...

    @abstractmethod
    async def get_by_status(self, status: DeliveryStatus) -> list[Delivery]: ...
