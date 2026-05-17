import pytest
from httpx import AsyncClient

from tests.integration.api.delivery.conftest import FakeDeliveryService

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# GET /deliveries
# ---------------------------------------------------------------------------


class TestGetDeliveries:
    async def test_director_gets_all(
        self, client: AsyncClient, delivery_svc: FakeDeliveryService
    ) -> None:
        await delivery_svc.create(order_id=10, executor_id=3, planned_date="2026-06-01")
        await delivery_svc.create(order_id=11, executor_id=3, planned_date="2026-06-02")
        r = await client.get("/api/v1/deliveries")
        assert r.status_code == 200
        assert len(r.json()) == 2

    async def test_delivery_user_sees_own_only(
        self,
        delivery_client: AsyncClient,
        delivery_svc: FakeDeliveryService,
    ) -> None:
        # executor_id=3 is the delivery user (id=3), executor_id=99 is someone else
        delivery_svc._deliveries.clear()
        delivery_svc._next_id = 1
        from datetime import date
        from src.domain.delivery.entities import Delivery
        d1 = Delivery(order_id=20, executor_id=3, planned_date=date(2026, 6, 1))
        d1.id = 1
        d2 = Delivery(order_id=21, executor_id=99, planned_date=date(2026, 6, 1))
        d2.id = 2
        delivery_svc._deliveries[1] = d1
        delivery_svc._deliveries[2] = d2
        r = await delivery_client.get("/api/v1/deliveries")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["order_id"] == 20

    async def test_unauthorized_returns_403(self, client: AsyncClient) -> None:
        from main import app
        from src.presentation.api.v1.auth.dependencies import get_current_user
        from src.domain.auth.entities import User
        from src.domain.auth.value_objects import Role
        from src.presentation.api.v1.delivery.dependencies import get_delivery_service
        from tests.integration.api.delivery.conftest import FakeDeliveryService
        from httpx import ASGITransport, AsyncClient as AC
        app.dependency_overrides[get_current_user] = lambda: User(
            username="prod", full_name="P", roles=[Role.production], id=5
        )
        app.dependency_overrides[get_delivery_service] = lambda: FakeDeliveryService()
        async with AC(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/api/v1/deliveries")
        app.dependency_overrides.clear()
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /deliveries/{id}
# ---------------------------------------------------------------------------


class TestGetDelivery:
    async def test_returns_delivery(
        self, client: AsyncClient, saved_delivery_id: int
    ) -> None:
        r = await client.get(f"/api/v1/deliveries/{saved_delivery_id}")
        assert r.status_code == 200
        assert r.json()["id"] == saved_delivery_id

    async def test_not_found(self, client: AsyncClient) -> None:
        r = await client.get("/api/v1/deliveries/999")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /deliveries
# ---------------------------------------------------------------------------


class TestCreateDelivery:
    async def test_creates_delivery(self, client: AsyncClient) -> None:
        r = await client.post("/api/v1/deliveries", json={
            "order_id": 5,
            "executor_id": 3,
            "planned_date": "2026-07-01",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["order_id"] == 5
        assert data["status"] == "pending"

    async def test_duplicate_order_returns_409(self, client: AsyncClient) -> None:
        await client.post("/api/v1/deliveries", json={
            "order_id": 7,
            "executor_id": 3,
            "planned_date": "2026-07-01",
        })
        r = await client.post("/api/v1/deliveries", json={
            "order_id": 7,
            "executor_id": 3,
            "planned_date": "2026-07-01",
        })
        assert r.status_code == 409

    async def test_production_user_cannot_create(self) -> None:
        from main import app
        from src.presentation.api.v1.auth.dependencies import get_current_user
        from src.domain.auth.entities import User
        from src.domain.auth.value_objects import Role
        from src.presentation.api.v1.delivery.dependencies import get_delivery_service
        from tests.integration.api.delivery.conftest import FakeDeliveryService
        from httpx import ASGITransport, AsyncClient as AC
        app.dependency_overrides[get_current_user] = lambda: User(
            username="prod", full_name="P", roles=[Role.production], id=5
        )
        app.dependency_overrides[get_delivery_service] = lambda: FakeDeliveryService()
        async with AC(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/api/v1/deliveries", json={
                "order_id": 8, "executor_id": 3, "planned_date": "2026-07-01"
            })
        app.dependency_overrides.clear()
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /deliveries/{id}/pick-up
# ---------------------------------------------------------------------------


class TestPickUp:
    async def test_pick_up(self, client: AsyncClient, saved_delivery_id: int) -> None:
        r = await client.post(f"/api/v1/deliveries/{saved_delivery_id}/pick-up")
        assert r.status_code == 204

    async def test_pick_up_wrong_status_returns_422(
        self, client: AsyncClient, saved_delivery_id: int
    ) -> None:
        await client.post(f"/api/v1/deliveries/{saved_delivery_id}/pick-up")
        r = await client.post(f"/api/v1/deliveries/{saved_delivery_id}/pick-up")
        assert r.status_code == 422

    async def test_not_found_returns_404(self, client: AsyncClient) -> None:
        r = await client.post("/api/v1/deliveries/999/pick-up")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /deliveries/{id}/start
# ---------------------------------------------------------------------------


class TestStartDelivery:
    async def test_start(self, client: AsyncClient, saved_delivery_id: int) -> None:
        await client.post(f"/api/v1/deliveries/{saved_delivery_id}/pick-up")
        r = await client.post(f"/api/v1/deliveries/{saved_delivery_id}/start")
        assert r.status_code == 204

    async def test_start_wrong_status_returns_422(
        self, client: AsyncClient, saved_delivery_id: int
    ) -> None:
        r = await client.post(f"/api/v1/deliveries/{saved_delivery_id}/start")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /deliveries/{id}/complete
# ---------------------------------------------------------------------------


class TestCompleteDelivery:
    async def test_complete(self, client: AsyncClient, saved_delivery_id: int) -> None:
        await client.post(f"/api/v1/deliveries/{saved_delivery_id}/pick-up")
        await client.post(f"/api/v1/deliveries/{saved_delivery_id}/start")
        r = await client.post(f"/api/v1/deliveries/{saved_delivery_id}/complete")
        assert r.status_code == 204

    async def test_complete_wrong_status_returns_422(
        self, client: AsyncClient, saved_delivery_id: int
    ) -> None:
        r = await client.post(f"/api/v1/deliveries/{saved_delivery_id}/complete")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /deliveries/{id}/cancel
# ---------------------------------------------------------------------------


class TestCancelDelivery:
    async def test_cancel_pending(self, client: AsyncClient, saved_delivery_id: int) -> None:
        r = await client.post(
            f"/api/v1/deliveries/{saved_delivery_id}/cancel",
            json={"reason": "customer refused"},
        )
        assert r.status_code == 204

    async def test_cancel_in_transit_returns_422(
        self, client: AsyncClient, saved_delivery_id: int
    ) -> None:
        await client.post(f"/api/v1/deliveries/{saved_delivery_id}/pick-up")
        await client.post(f"/api/v1/deliveries/{saved_delivery_id}/start")
        r = await client.post(
            f"/api/v1/deliveries/{saved_delivery_id}/cancel",
            json={"reason": "too late"},
        )
        assert r.status_code == 422

    async def test_cancel_empty_reason_returns_422(
        self, client: AsyncClient, saved_delivery_id: int
    ) -> None:
        r = await client.post(
            f"/api/v1/deliveries/{saved_delivery_id}/cancel",
            json={"reason": ""},
        )
        assert r.status_code == 422

    async def test_not_found_returns_404(self, client: AsyncClient) -> None:
        r = await client.post(
            "/api/v1/deliveries/999/cancel",
            json={"reason": "test"},
        )
        assert r.status_code == 404
