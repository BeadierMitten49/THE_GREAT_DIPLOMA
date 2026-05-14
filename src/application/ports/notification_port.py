from abc import ABC, abstractmethod


class INotificationService(ABC):
    @abstractmethod
    async def send(self, user_id: int, message: str) -> None: ...
