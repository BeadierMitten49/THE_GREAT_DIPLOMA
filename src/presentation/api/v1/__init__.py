from fastapi import APIRouter

from src.presentation.api.v1.references import router as references_router

router = APIRouter()

router.include_router(references_router)
