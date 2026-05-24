from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.domain.notifications.entities import Notification
from src.domain.notifications.value_objects import NotificationEvent
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.notifications.dependencies import get_notification_service


class FakeNotificationService:
    def __init__(self) -> None:
        self._store: list[Notification] = []
        self._next_id = 1

    def _add(self, recipient_id: int, event_type: NotificationEvent, title: str, body: str) -> Notification:
        n = Notification(
            id=self._next_id,
            recipient_id=recipient_id,
            event_type=event_type,
            title=title,
            body=body,
            created_at=datetime.now(timezone.utc),
        )
        self._store.append(n)
        self._next_id += 1
        return n

    async def get_my_notifications(self, user_id: int, *, unread_only: bool = False) -> list[Notification]:
        result = [n for n in self._store if n.recipient_id == user_id]
        if unread_only:
            result = [n for n in result if not n.is_read]
        return sorted(result, key=lambda n: n.created_at, reverse=True)

    async def get_recent(self, limit: int = 20) -> list[Notification]:
        return sorted(self._store, key=lambda n: n.created_at, reverse=True)[:limit]

    async def get_unread_count(self, user_id: int) -> int:
        return len([n for n in self._store if n.recipient_id == user_id and not n.is_read])

    async def mark_read(self, notification_id: int) -> None:
        for n in self._store:
            if n.id == notification_id:
                n.is_read = True
                break

    async def mark_all_read(self, user_id: int) -> None:
        for n in self._store:
            if n.recipient_id == user_id:
                n.is_read = True


def _make_director() -> User:
    return User(username="director", full_name="Director", roles=[Role.director], id=1)


def _make_worker() -> User:
    return User(username="worker", full_name="Worker", roles=[Role.production], id=2)


@pytest.fixture
def notification_svc() -> FakeNotificationService:
    return FakeNotificationService()


@pytest_asyncio.fixture
async def client(notification_svc: FakeNotificationService):
    app.dependency_overrides[get_current_user] = lambda: _make_director()
    app.dependency_overrides[get_notification_service] = lambda: notification_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def worker_client(notification_svc: FakeNotificationService):
    app.dependency_overrides[get_current_user] = lambda: _make_worker()
    app.dependency_overrides[get_notification_service] = lambda: notification_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
