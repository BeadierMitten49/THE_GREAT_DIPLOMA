from fastapi import APIRouter

from src.presentation.api.v1.warehouse.packaging_stock import router as packaging_stock_router
from src.presentation.api.v1.warehouse.product_stock import router as product_stock_router
from src.presentation.api.v1.warehouse.raw_material_stock import router as raw_material_stock_router

router = APIRouter(prefix="/warehouse")

router.include_router(raw_material_stock_router)
router.include_router(packaging_stock_router)
router.include_router(product_stock_router)
