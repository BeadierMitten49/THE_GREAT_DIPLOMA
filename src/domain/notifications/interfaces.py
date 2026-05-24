from abc import abstractmethod

from src.domain.notifications.entities import Notification
from src.domain.shared.repository import IPlainRepository


class INotificationRepository(IPlainRepository[Notification]):
    @abstractmethod
    async def get_by_recipient(
        self, recipient_id: int, *, unread_only: bool = False,
    ) -> list[Notification]: ...

    @abstractmethod
    async def mark_as_read(self, id: int) -> None: ...

    @abstractmethod
    async def mark_all_as_read(self, recipient_id: int) -> None: ...

    @abstractmethod
    async def get_recent(self, limit: int = 20) -> list[Notification]: ...
