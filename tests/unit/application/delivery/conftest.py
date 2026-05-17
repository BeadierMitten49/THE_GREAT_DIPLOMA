from datetime import date

import pytest

from src.domain.delivery.entities import Delivery
from src.domain.delivery.value_objects import DeliveryStatus


class FakeDeliveryRepository:
    def __init__(self) -> None:
        self._store: dict[int, Delivery] = {}
        self._next_id = 1

    async def get_by_id(self, id: int) -> Delivery | None:
        return self._store.get(id)

    async def save(self, entity: Delivery) -> int:
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._store[entity.id] = entity
        return entity.id

    async def get_all(self) -> list[Delivery]:
        return list(self._store.values())

    async def get_by_order(self, order_id: int) -> Delivery | None:
        for d in self._store.values():
            if d.order_id == order_id:
                return d
        return None

    async def get_by_executor(self, executor_id: int) -> list[Delivery]:
        return [d for d in self._store.values() if d.executor_id == executor_id]

    async def get_by_status(self, status: DeliveryStatus) -> list[Delivery]:
        return [d for d in self._store.values() if d.status == status]


def _make_delivery(**kwargs) -> Delivery:
    defaults = dict(
        order_id=1,
        executor_id=2,
        planned_date=date(2026, 6, 1),
    )
    defaults.update(kwargs)
    return Delivery(**defaults)


@pytest.fixture
def delivery_repo() -> FakeDeliveryRepository:
    return FakeDeliveryRepository()


@pytest.fixture
async def saved_delivery(delivery_repo: FakeDeliveryRepository) -> Delivery:
    delivery = _make_delivery()
    await delivery_repo.save(delivery)
    return delivery
