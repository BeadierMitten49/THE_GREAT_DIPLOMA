from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.delivery.entities import Delivery
from src.domain.delivery.value_objects import DeliveryStatus
from src.infrastructure.db.repositories.delivery import DeliveryRepository

pytestmark = pytest.mark.integration


def _make_delivery(**kwargs) -> Delivery:
    defaults = dict(
        order_id=1,
        executor_id=2,
        planned_date=date(2026, 6, 1),
    )
    defaults.update(kwargs)
    return Delivery(**defaults)


class TestDeliveryRepository:
    async def test_save_and_get_by_id(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        delivery = _make_delivery()
        delivery_id = await repo.save(delivery)
        fetched = await repo.get_by_id(delivery_id)
        assert fetched is not None
        assert fetched.order_id == 1
        assert fetched.status == DeliveryStatus.pending

    async def test_save_updates_existing(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        delivery = _make_delivery()
        await repo.save(delivery)
        delivery.pick_up()
        await repo.save(delivery)
        fetched = await repo.get_by_id(delivery.id)
        assert fetched.status == DeliveryStatus.picked_up

    async def test_get_by_id_not_found(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        result = await repo.get_by_id(999)
        assert result is None

    async def test_get_all(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        await repo.save(_make_delivery(order_id=10))
        await repo.save(_make_delivery(order_id=11))
        all_deliveries = await repo.get_all()
        order_ids = {d.order_id for d in all_deliveries}
        assert {10, 11}.issubset(order_ids)

    async def test_get_by_order(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        await repo.save(_make_delivery(order_id=20))
        result = await repo.get_by_order(20)
        assert result is not None
        assert result.order_id == 20

    async def test_get_by_order_not_found(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        result = await repo.get_by_order(9999)
        assert result is None

    async def test_get_by_executor(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        await repo.save(_make_delivery(order_id=30, executor_id=5))
        await repo.save(_make_delivery(order_id=31, executor_id=5))
        await repo.save(_make_delivery(order_id=32, executor_id=6))
        result = await repo.get_by_executor(5)
        assert len(result) == 2
        assert all(d.executor_id == 5 for d in result)

    async def test_get_by_status(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        d1 = _make_delivery(order_id=40)
        d2 = _make_delivery(order_id=41)
        await repo.save(d1)
        await repo.save(d2)
        d1.pick_up()
        await repo.save(d1)
        result = await repo.get_by_status(DeliveryStatus.picked_up)
        assert any(d.order_id == 40 for d in result)
        assert all(d.status == DeliveryStatus.picked_up for d in result)

    async def test_full_state_machine_persisted(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        delivery = _make_delivery(order_id=50)
        await repo.save(delivery)

        delivery.pick_up()
        await repo.save(delivery)
        delivery.start()
        await repo.save(delivery)
        delivery.complete()
        await repo.save(delivery)

        fetched = await repo.get_by_id(delivery.id)
        assert fetched.status == DeliveryStatus.completed
        assert fetched.started_at is not None
        assert fetched.completed_at is not None

    async def test_cancel_persists_reason(self, session: AsyncSession) -> None:
        repo = DeliveryRepository(session)
        delivery = _make_delivery(order_id=60)
        await repo.save(delivery)
        delivery.cancel(reason="driver sick")
        await repo.save(delivery)
        fetched = await repo.get_by_id(delivery.id)
        assert fetched.status == DeliveryStatus.cancelled
        assert fetched.cancellation_reason == "driver sick"
