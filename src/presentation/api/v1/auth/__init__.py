from fastapi import APIRouter

from src.presentation.api.v1.auth.auth import router as auth_router
from src.presentation.api.v1.auth.users import router as users_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
