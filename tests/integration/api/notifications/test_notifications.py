import pytest
from httpx import AsyncClient

from src.domain.notifications.value_objects import NotificationEvent
from tests.integration.api.notifications.conftest import FakeNotificationService


@pytest.mark.asyncio
class TestListNotifications:
    async def test_empty_list(self, client: AsyncClient):
        r = await client.get("/api/v1/notifications")
        assert r.status_code == 200
        assert r.json() == []

    async def test_returns_user_notifications(
        self, client: AsyncClient, notification_svc: FakeNotificationService,
    ):
        notification_svc._add(1, NotificationEvent.task_completed, "Задача завершена", "Задача #1 завершена")
        notification_svc._add(2, NotificationEvent.task_stopped, "Задача остановлена", "Не для директора")

        r = await client.get("/api/v1/notifications")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["title"] == "Задача завершена"
        assert data[0]["event_type"] == "task_completed"
        assert data[0]["is_read"] is False

    async def test_unread_only_filter(
        self, client: AsyncClient, notification_svc: FakeNotificationService,
    ):
        n = notification_svc._add(1, NotificationEvent.critical_stock, "Критический остаток", "Сахар")
        notification_svc._add(1, NotificationEvent.delivery_completed, "Доставлено", "Доставка #1")
        n.is_read = True

        r = await client.get("/api/v1/notifications", params={"unread_only": True})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["title"] == "Доставлено"


@pytest.mark.asyncio
class TestUnreadCount:
    async def test_zero_when_empty(self, client: AsyncClient):
        r = await client.get("/api/v1/notifications/unread-count")
        assert r.status_code == 200
        assert r.json()["count"] == 0

    async def test_counts_unread(
        self, client: AsyncClient, notification_svc: FakeNotificationService,
    ):
        notification_svc._add(1, NotificationEvent.task_completed, "T1", "B1")
        notification_svc._add(1, NotificationEvent.task_completed, "T2", "B2")
        n = notification_svc._add(1, NotificationEvent.task_completed, "T3", "B3")
        n.is_read = True

        r = await client.get("/api/v1/notifications/unread-count")
        assert r.status_code == 200
        assert r.json()["count"] == 2


@pytest.mark.asyncio
class TestRecentNotifications:
    async def test_director_can_access(
        self, client: AsyncClient, notification_svc: FakeNotificationService,
    ):
        notification_svc._add(1, NotificationEvent.task_completed, "T1", "B1")
        notification_svc._add(2, NotificationEvent.task_stopped, "T2", "B2")

        r = await client.get("/api/v1/notifications/recent")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2

    async def test_worker_forbidden(
        self, worker_client: AsyncClient, notification_svc: FakeNotificationService,
    ):
        r = await worker_client.get("/api/v1/notifications/recent")
        assert r.status_code == 403


@pytest.mark.asyncio
class TestMarkRead:
    async def test_mark_single_read(
        self, client: AsyncClient, notification_svc: FakeNotificationService,
    ):
        notification_svc._add(1, NotificationEvent.critical_stock, "Alert", "Low stock")

        r = await client.post("/api/v1/notifications/1/read")
        assert r.status_code == 200

        r = await client.get("/api/v1/notifications/unread-count")
        assert r.json()["count"] == 0

    async def test_mark_all_read(
        self, client: AsyncClient, notification_svc: FakeNotificationService,
    ):
        notification_svc._add(1, NotificationEvent.task_completed, "T1", "B1")
        notification_svc._add(1, NotificationEvent.delivery_completed, "T2", "B2")
        notification_svc._add(1, NotificationEvent.critical_stock, "T3", "B3")

        r = await client.post("/api/v1/notifications/read-all")
        assert r.status_code == 200

        r = await client.get("/api/v1/notifications/unread-count")
        assert r.json()["count"] == 0


@pytest.mark.asyncio
class TestNotificationResponse:
    async def test_response_schema(
        self, client: AsyncClient, notification_svc: FakeNotificationService,
    ):
        notification_svc._add(
            1, NotificationEvent.order_shipped, "Заказ отгружен", "Заказ №5 готов к доставке"
        )

        r = await client.get("/api/v1/notifications")
        assert r.status_code == 200
        n = r.json()[0]
        assert "id" in n
        assert "recipient_id" in n
        assert "event_type" in n
        assert "title" in n
        assert "body" in n
        assert "is_read" in n
        assert "created_at" in n
        assert n["event_type"] == "order_shipped"
        assert n["related_entity_type"] is None
        assert n["related_entity_id"] is None
