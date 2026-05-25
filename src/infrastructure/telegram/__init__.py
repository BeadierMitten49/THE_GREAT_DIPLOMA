from src.application.ports.telegram_port import ITelegramClient
from src.infrastructure.config import settings
from src.infrastructure.telegram.client import TelegramClient

_instance: ITelegramClient | None = None


def get_telegram_client() -> ITelegramClient | None:
    """Returns the global TelegramClient singleton, or None if token is not configured."""
    global _instance
    if _instance is None and settings.telegram_bot_token:
        _instance = TelegramClient(settings.telegram_bot_token)
    return _instance
