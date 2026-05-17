from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.application.shared.exceptions import AlreadyExistsError, NotFoundError
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.domain.delivery.entities import Delivery
from src.domain.delivery.value_objects import DeliveryStatus
from src.domain.shared.exceptions import InvalidFieldError
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.delivery.dependencies import get_delivery_service


class FakeDeliveryService:
    def __init__(self) -> None:
        self._deliveries: dict[int, Delivery] = {}
        self._next_id = 1

    def _make_delivery(self, **kwargs) -> Delivery:
        defaults = dict(
            order_id=1,
            executor_id=2,
            planned_date=date(2026, 6, 1),
        )
        defaults.update(kwargs)
        d = Delivery(**defaults)
        d.id = self._next_id
        self._next_id += 1
        return d

    async def get(self, delivery_id: int) -> Delivery:
        d = self._deliveries.get(delivery_id)
        if d is None:
            raise NotFoundError("Delivery", delivery_id)
        return d

    async def get_all(
        self,
        executor_id: int | None = None,
        status: DeliveryStatus | None = None,
    ) -> list[Delivery]:
        deliveries = list(self._deliveries.values())
        if executor_id is not None:
            deliveries = [d for d in deliveries if d.executor_id == executor_id]
        if status is not None:
            deliveries = [d for d in deliveries if d.status == status]
        return deliveries

    async def create(self, order_id: int, executor_id: int, planned_date: date) -> int:
        for d in self._deliveries.values():
            if d.order_id == order_id:
                raise AlreadyExistsError("Delivery", "order_id", str(order_id))
        delivery = self._make_delivery(
            order_id=order_id,
            executor_id=executor_id,
            planned_date=planned_date,
        )
        self._deliveries[delivery.id] = delivery
        return delivery.id

    async def pick_up(self, delivery_id: int) -> None:
        d = await self.get(delivery_id)
        d.pick_up()

    async def start(self, delivery_id: int) -> None:
        d = await self.get(delivery_id)
        d.start()

    async def complete(self, delivery_id: int) -> None:
        d = await self.get(delivery_id)
        d.complete()

    async def cancel(self, delivery_id: int, reason: str) -> None:
        d = await self.get(delivery_id)
        d.cancel(reason=reason)


def _make_director() -> User:
    return User(username="director", full_name="Director", roles=[Role.director], id=1)


def _make_delivery_user() -> User:
    return User(username="driver", full_name="Driver", roles=[Role.delivery], id=3)


@pytest.fixture
def delivery_svc() -> FakeDeliveryService:
    return FakeDeliveryService()


@pytest_asyncio.fixture
async def client(delivery_svc: FakeDeliveryService) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: _make_director()
    app.dependency_overrides[get_delivery_service] = lambda: delivery_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def delivery_client(delivery_svc: FakeDeliveryService) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: _make_delivery_user()
    app.dependency_overrides[get_delivery_service] = lambda: delivery_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def saved_delivery_id(client: AsyncClient) -> int:
    r = await client.post("/api/v1/deliveries", json={
        "order_id": 1,
        "executor_id": 3,
        "planned_date": "2026-06-01",
    })
    assert r.status_code == 201
    return r.json()["id"]
