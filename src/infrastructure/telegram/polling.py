import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.infrastructure.telegram.client import TelegramClient
from src.infrastructure.db.repositories.auth import UserRepository

logger = logging.getLogger(__name__)


async def run_polling(
    tg_client: TelegramClient,
    session_factory: async_sessionmaker,
) -> None:
    """Long-polling loop that handles /start commands to bind telegram_id."""
    logger.info("Telegram polling started")
    offset = 0

    while True:
        try:
            updates = await tg_client.get_updates(offset=offset, timeout=30)
        except Exception:
            logger.exception("Polling error, retrying in 5s")
            await asyncio.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            await _handle_update(update, tg_client, session_factory)


async def _handle_update(
    update: dict,
    tg_client: TelegramClient,
    session_factory: async_sessionmaker,
) -> None:
    message = update.get("message")
    if not message:
        return

    text = (message.get("text") or "").strip()
    if not text.startswith("/start"):
        return

    from_user = message.get("from", {})
    tg_username = from_user.get("username")
    chat_id = message["chat"]["id"]

    if not tg_username:
        await tg_client.send_message(
            chat_id,
            "У вас не установлен username в Telegram. "
            "Установите его в настройках Telegram и повторите /start.",
        )
        return

    async with session_factory() as session:
        repo = UserRepository(session)
        users = await repo.get_all(include_inactive=False)
        matched = None
        for user in users:
            if user.telegram_username and user.telegram_username.lower().lstrip("@") == tg_username.lower():
                matched = user
                break

        if not matched:
            await tg_client.send_message(
                chat_id,
                f"Пользователь с Telegram @{tg_username} не найден в системе. "
                "Попросите директора указать ваш Telegram-username в настройках.",
            )
            return

        if matched.telegram_id == chat_id:
            await tg_client.send_message(chat_id, "Вы уже привязаны. Уведомления будут приходить сюда.")
            return

        matched.set_telegram_id(chat_id)
        await repo.save(matched)
        await session.commit()

    logger.info("Telegram bound: user=%s tg_id=%d", matched.username, chat_id)
    await tg_client.send_message(
        chat_id,
        f"Привязка выполнена! {matched.full_name}, вы будете получать уведомления системы АИС «Ярко».",
    )
