from datetime import date

import pytest

from src.application.delivery.use_cases import (
    cancel_delivery,
    complete_delivery,
    create_delivery,
    get_deliveries,
    get_delivery,
    pick_up_order,
    start_delivery,
)
from src.application.shared.exceptions import NotFoundError
from src.domain.delivery.entities import Delivery
from src.domain.delivery.value_objects import DeliveryStatus
from src.domain.shared.exceptions import InvalidFieldError

from tests.unit.application.delivery.conftest import (
    FakeDeliveryRepository,
    _make_delivery,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# get_delivery
# ---------------------------------------------------------------------------


class TestGetDelivery:
    async def test_returns_delivery(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        result = await get_delivery(saved_delivery.id, delivery_repo)
        assert result.id == saved_delivery.id

    async def test_not_found_raises(self, delivery_repo: FakeDeliveryRepository) -> None:
        with pytest.raises(NotFoundError):
            await get_delivery(999, delivery_repo)


# ---------------------------------------------------------------------------
# get_deliveries
# ---------------------------------------------------------------------------


class TestGetDeliveries:
    async def test_returns_all(self, delivery_repo: FakeDeliveryRepository) -> None:
        d1 = _make_delivery(order_id=1)
        d2 = _make_delivery(order_id=2)
        await delivery_repo.save(d1)
        await delivery_repo.save(d2)
        result = await get_deliveries(delivery_repo)
        assert len(result) == 2

    async def test_filter_by_executor(self, delivery_repo: FakeDeliveryRepository) -> None:
        d1 = _make_delivery(order_id=1, executor_id=10)
        d2 = _make_delivery(order_id=2, executor_id=20)
        await delivery_repo.save(d1)
        await delivery_repo.save(d2)
        result = await get_deliveries(delivery_repo, executor_id=10)
        assert len(result) == 1
        assert result[0].executor_id == 10

    async def test_filter_by_status(self, delivery_repo: FakeDeliveryRepository) -> None:
        d1 = _make_delivery(order_id=1)
        d2 = _make_delivery(order_id=2)
        await delivery_repo.save(d1)
        await delivery_repo.save(d2)
        d1.pick_up()
        await delivery_repo.save(d1)
        result = await get_deliveries(delivery_repo, status=DeliveryStatus.picked_up)
        assert len(result) == 1
        assert result[0].order_id == 1


# ---------------------------------------------------------------------------
# create_delivery
# ---------------------------------------------------------------------------


class TestCreateDelivery:
    async def test_creates_with_pending_status(
        self, delivery_repo: FakeDeliveryRepository
    ) -> None:
        from src.application.delivery.dto import CreateDeliveryDTO
        dto = CreateDeliveryDTO(order_id=5, executor_id=3, planned_date=date(2026, 7, 1))
        delivery_id = await create_delivery(dto, delivery_repo)
        delivery = await delivery_repo.get_by_id(delivery_id)
        assert delivery is not None
        assert delivery.status == DeliveryStatus.pending
        assert delivery.order_id == 5

    async def test_duplicate_order_raises(self, delivery_repo: FakeDeliveryRepository) -> None:
        from src.application.delivery.dto import CreateDeliveryDTO
        dto = CreateDeliveryDTO(order_id=5, executor_id=3, planned_date=date(2026, 7, 1))
        await create_delivery(dto, delivery_repo)
        from src.application.shared.exceptions import AlreadyExistsError
        with pytest.raises(AlreadyExistsError):
            await create_delivery(dto, delivery_repo)


# ---------------------------------------------------------------------------
# pick_up_order
# ---------------------------------------------------------------------------


class TestPickUpOrder:
    async def test_sets_picked_up(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        await pick_up_order(saved_delivery.id, delivery_repo)
        delivery = await delivery_repo.get_by_id(saved_delivery.id)
        assert delivery.status == DeliveryStatus.picked_up

    async def test_not_found_raises(self, delivery_repo: FakeDeliveryRepository) -> None:
        with pytest.raises(NotFoundError):
            await pick_up_order(999, delivery_repo)

    async def test_wrong_status_raises(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        saved_delivery.cancel(reason="test")
        await delivery_repo.save(saved_delivery)
        with pytest.raises(InvalidFieldError):
            await pick_up_order(saved_delivery.id, delivery_repo)


# ---------------------------------------------------------------------------
# start_delivery
# ---------------------------------------------------------------------------


class TestStartDelivery:
    async def test_sets_in_transit(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        saved_delivery.pick_up()
        await delivery_repo.save(saved_delivery)
        await start_delivery(saved_delivery.id, delivery_repo)
        delivery = await delivery_repo.get_by_id(saved_delivery.id)
        assert delivery.status == DeliveryStatus.in_transit

    async def test_not_found_raises(self, delivery_repo: FakeDeliveryRepository) -> None:
        with pytest.raises(NotFoundError):
            await start_delivery(999, delivery_repo)

    async def test_wrong_status_raises(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        with pytest.raises(InvalidFieldError):
            await start_delivery(saved_delivery.id, delivery_repo)


# ---------------------------------------------------------------------------
# complete_delivery
# ---------------------------------------------------------------------------


class TestCompleteDelivery:
    async def test_sets_completed(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        saved_delivery.pick_up()
        saved_delivery.start()
        await delivery_repo.save(saved_delivery)
        await complete_delivery(saved_delivery.id, delivery_repo)
        delivery = await delivery_repo.get_by_id(saved_delivery.id)
        assert delivery.status == DeliveryStatus.completed

    async def test_not_found_raises(self, delivery_repo: FakeDeliveryRepository) -> None:
        with pytest.raises(NotFoundError):
            await complete_delivery(999, delivery_repo)

    async def test_wrong_status_raises(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        with pytest.raises(InvalidFieldError):
            await complete_delivery(saved_delivery.id, delivery_repo)


# ---------------------------------------------------------------------------
# cancel_delivery
# ---------------------------------------------------------------------------


class TestCancelDelivery:
    async def test_sets_cancelled(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        await cancel_delivery(saved_delivery.id, "customer refused", delivery_repo)
        delivery = await delivery_repo.get_by_id(saved_delivery.id)
        assert delivery.status == DeliveryStatus.cancelled
        assert delivery.cancellation_reason == "customer refused"

    async def test_not_found_raises(self, delivery_repo: FakeDeliveryRepository) -> None:
        with pytest.raises(NotFoundError):
            await cancel_delivery(999, "reason", delivery_repo)

    async def test_wrong_status_raises(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        saved_delivery.pick_up()
        saved_delivery.start()
        await delivery_repo.save(saved_delivery)
        with pytest.raises(InvalidFieldError):
            await cancel_delivery(saved_delivery.id, "too late", delivery_repo)

    async def test_empty_reason_raises(
        self, delivery_repo: FakeDeliveryRepository, saved_delivery: Delivery
    ) -> None:
        with pytest.raises(InvalidFieldError):
            await cancel_delivery(saved_delivery.id, "", delivery_repo)
