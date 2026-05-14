from fastapi import FastAPI

from src.infrastructure.logging_setup import setup_logging
from src.presentation.api.exception_handlers import register_exception_handlers
from src.presentation.api.v1 import router as api_router

setup_logging()

app = FastAPI(
    title="АИС «Ярко»",
    description="Production Management System",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")
register_exception_handlers(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
