from fastapi import APIRouter

from src.presentation.api.v1.auth import router as auth_router
from src.presentation.api.v1.delivery import router as delivery_router
from src.presentation.api.v1.orders import router as orders_router
from src.presentation.api.v1.references import router as references_router
from src.presentation.api.v1.tasks import router as tasks_router
from src.presentation.api.v1.warehouse import router as warehouse_router

router = APIRouter()

router.include_router(references_router)
router.include_router(auth_router)
router.include_router(warehouse_router)
router.include_router(orders_router)
router.include_router(tasks_router)
router.include_router(delivery_router)
