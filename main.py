from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.application.references.exceptions import AlreadyExistsError, NotFoundError
from src.domain.references.exceptions import InvalidFieldError
from src.infrastructure.logging_setup import setup_logging
from src.presentation.api.v1 import router as api_router

setup_logging()

app = FastAPI(
    title="АИС «Ярко»",
    description="Production Management System",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(AlreadyExistsError)
async def already_exists_handler(request: Request, exc: AlreadyExistsError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InvalidFieldError)
async def invalid_field_handler(request: Request, exc: InvalidFieldError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
