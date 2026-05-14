from fastapi import APIRouter

from src.presentation.api.v1.auth import router as auth_router
from src.presentation.api.v1.references import router as references_router

router = APIRouter()

router.include_router(references_router)
router.include_router(auth_router)
