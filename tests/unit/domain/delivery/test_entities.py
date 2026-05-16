from datetime import date

import pytest

from src.domain.delivery.entities import Delivery
from src.domain.delivery.value_objects import DeliveryStatus
from src.domain.shared.exceptions import InvalidFieldError

pytestmark = pytest.mark.unit


def _make_delivery(**kwargs) -> Delivery:
    defaults = dict(
        order_id=1,
        executor_id=2,
        planned_date=date(2026, 6, 1),
    )
    defaults.update(kwargs)
    return Delivery(**defaults)


# ---------------------------------------------------------------------------
# Value object
# ---------------------------------------------------------------------------


class TestDeliveryStatus:
    def test_all_values(self) -> None:
        assert DeliveryStatus.pending == "pending"
        assert DeliveryStatus.picked_up == "picked_up"
        assert DeliveryStatus.in_transit == "in_transit"
        assert DeliveryStatus.completed == "completed"
        assert DeliveryStatus.cancelled == "cancelled"


# ---------------------------------------------------------------------------
# pick_up — pending → picked_up
# ---------------------------------------------------------------------------


class TestDeliveryPickUp:
    def test_pick_up_sets_picked_up(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        assert delivery.status == DeliveryStatus.picked_up

    def test_pick_up_from_in_transit_raises(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        with pytest.raises(InvalidFieldError):
            delivery.pick_up()

    def test_pick_up_from_completed_raises(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        delivery.complete()
        with pytest.raises(InvalidFieldError):
            delivery.pick_up()

    def test_pick_up_from_cancelled_raises(self) -> None:
        delivery = _make_delivery()
        delivery.cancel(reason="test")
        with pytest.raises(InvalidFieldError):
            delivery.pick_up()


# ---------------------------------------------------------------------------
# start — picked_up → in_transit
# ---------------------------------------------------------------------------


class TestDeliveryStart:
    def test_start_sets_in_transit(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        assert delivery.status == DeliveryStatus.in_transit

    def test_start_sets_started_at(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        assert delivery.started_at is not None

    def test_start_from_pending_raises(self) -> None:
        delivery = _make_delivery()
        with pytest.raises(InvalidFieldError):
            delivery.start()

    def test_start_from_completed_raises(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        delivery.complete()
        with pytest.raises(InvalidFieldError):
            delivery.start()

    def test_start_from_cancelled_raises(self) -> None:
        delivery = _make_delivery()
        delivery.cancel(reason="test")
        with pytest.raises(InvalidFieldError):
            delivery.start()


# ---------------------------------------------------------------------------
# complete — in_transit → completed
# ---------------------------------------------------------------------------


class TestDeliveryComplete:
    def test_complete_sets_completed(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        delivery.complete()
        assert delivery.status == DeliveryStatus.completed

    def test_complete_sets_completed_at(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        delivery.complete()
        assert delivery.completed_at is not None

    def test_complete_from_pending_raises(self) -> None:
        delivery = _make_delivery()
        with pytest.raises(InvalidFieldError):
            delivery.complete()

    def test_complete_from_picked_up_raises(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        with pytest.raises(InvalidFieldError):
            delivery.complete()

    def test_complete_from_cancelled_raises(self) -> None:
        delivery = _make_delivery()
        delivery.cancel(reason="test")
        with pytest.raises(InvalidFieldError):
            delivery.complete()


# ---------------------------------------------------------------------------
# cancel — pending / picked_up → cancelled
# ---------------------------------------------------------------------------


class TestDeliveryCancel:
    def test_cancel_from_pending(self) -> None:
        delivery = _make_delivery()
        delivery.cancel(reason="customer refused")
        assert delivery.status == DeliveryStatus.cancelled

    def test_cancel_from_picked_up(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.cancel(reason="car broke")
        assert delivery.status == DeliveryStatus.cancelled

    def test_cancel_stores_reason(self) -> None:
        delivery = _make_delivery()
        delivery.cancel(reason="no fuel")
        assert delivery.cancellation_reason == "no fuel"

    def test_cancel_from_in_transit_raises(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        with pytest.raises(InvalidFieldError):
            delivery.cancel(reason="too late")

    def test_cancel_from_completed_raises(self) -> None:
        delivery = _make_delivery()
        delivery.pick_up()
        delivery.start()
        delivery.complete()
        with pytest.raises(InvalidFieldError):
            delivery.cancel(reason="too late")

    def test_cancel_from_cancelled_raises(self) -> None:
        delivery = _make_delivery()
        delivery.cancel(reason="first")
        with pytest.raises(InvalidFieldError):
            delivery.cancel(reason="second")

    def test_cancel_requires_reason(self) -> None:
        delivery = _make_delivery()
        with pytest.raises(InvalidFieldError):
            delivery.cancel(reason="")
