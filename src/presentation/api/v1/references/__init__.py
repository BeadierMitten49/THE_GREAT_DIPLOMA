from fastapi import APIRouter

from src.presentation.api.v1.references.customers import router as customers_router
from src.presentation.api.v1.references.packaging import router as packaging_router
from src.presentation.api.v1.references.products import router as products_router
from src.presentation.api.v1.references.raw_materials import router as raw_materials_router

router = APIRouter(prefix="/references")

router.include_router(customers_router)
router.include_router(products_router)
router.include_router(raw_materials_router)
router.include_router(packaging_router)
