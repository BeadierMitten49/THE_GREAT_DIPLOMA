import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.logging_setup import setup_logging
from src.presentation.api.exception_handlers import register_exception_handlers
from src.presentation.api.v1 import router as api_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    from src.infrastructure.telegram import get_telegram_client
    from src.infrastructure.telegram.polling import run_polling
    from src.infrastructure.db.session import AsyncSessionFactory

    tg_client = get_telegram_client()
    polling_task = None

    if tg_client is None:
        logger.info("TELEGRAM_BOT_TOKEN not set — Telegram features disabled")
    else:
        bot_info = await tg_client.get_me()
        if bot_info:
            logger.info("Telegram bot connected: @%s", bot_info.get("username"))
        else:
            logger.warning("Telegram bot token is set but getMe failed — polling will retry")
        polling_task = asyncio.create_task(run_polling(tg_client, AsyncSessionFactory))

    yield

    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
        logger.info("Telegram polling stopped")


app = FastAPI(
    title="АИС «Ярко»",
    description="Production Management System",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")
register_exception_handlers(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
