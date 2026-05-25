from abc import ABC, abstractmethod


class ITelegramClient(ABC):
    @abstractmethod
    async def send_message(self, chat_id: int, text: str) -> bool:
        """Send a message. Returns True on success, False on failure."""
        ...

    @abstractmethod
    async def get_me(self) -> dict | None:
        """Check bot connectivity. Returns bot info or None on failure."""
        ...
