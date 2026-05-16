from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.application.orders.exceptions import InsufficientStockError
from src.application.references.exceptions import AlreadyExistsError
from src.application.shared.exceptions import NotFoundError
from src.domain.shared.exceptions import InvalidFieldError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(AlreadyExistsError)
    async def already_exists_handler(request: Request, exc: AlreadyExistsError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InvalidFieldError)
    async def invalid_field_handler(request: Request, exc: InvalidFieldError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_handler(request: Request, exc: InsufficientStockError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
