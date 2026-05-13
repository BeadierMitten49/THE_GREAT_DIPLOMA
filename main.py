from fastapi import FastAPI

from src.presentation.api.v1 import router as api_router

app = FastAPI(
    title="АИС «Ярко»",
    description="Production Management System",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
