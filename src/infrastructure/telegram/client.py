import logging

import httpx

from src.application.ports.telegram_port import ITelegramClient

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0


class TelegramClient(ITelegramClient):
    def __init__(self, token: str) -> None:
        self._base_url = f"https://api.telegram.org/bot{token}"

    async def send_message(self, chat_id: int, text: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._base_url}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                )
            if resp.status_code == 200 and resp.json().get("ok"):
                return True
            logger.warning("Telegram sendMessage failed: %s", resp.text)
            return False
        except Exception:
            logger.exception("Telegram sendMessage error")
            return False

    async def get_me(self) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(f"{self._base_url}/getMe")
            data = resp.json()
            if data.get("ok"):
                return data["result"]
            return None
        except Exception:
            logger.exception("Telegram getMe error")
            return None

    async def get_updates(self, offset: int = 0, timeout: int = 30) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=timeout + 5) as client:
                resp = await client.get(
                    f"{self._base_url}/getUpdates",
                    params={"offset": offset, "timeout": timeout, "allowed_updates": '["message"]'},
                )
            data = resp.json()
            if data.get("ok"):
                return data.get("result", [])
            return []
        except Exception:
            logger.exception("Telegram getUpdates error")
            return []
