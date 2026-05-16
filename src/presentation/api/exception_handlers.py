from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.application.references.exceptions import AlreadyExistsError
from src.application.references.exceptions import NotFoundError as ReferencesNotFoundError
from src.application.warehouse.exceptions import NotFoundError as WarehouseNotFoundError
from src.domain.shared.exceptions import InvalidFieldError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ReferencesNotFoundError)
    async def references_not_found_handler(request: Request, exc: ReferencesNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(WarehouseNotFoundError)
    async def warehouse_not_found_handler(request: Request, exc: WarehouseNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(AlreadyExistsError)
    async def already_exists_handler(request: Request, exc: AlreadyExistsError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InvalidFieldError)
    async def invalid_field_handler(request: Request, exc: InvalidFieldError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
