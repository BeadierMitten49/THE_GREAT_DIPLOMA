from fastapi import APIRouter, Depends, status

from src.domain.auth.entities import User
from src.presentation.api.v1.auth.dependencies import get_current_user, get_user_service
from src.presentation.api.v1.auth.schemas import (
    BindTelegramRequest,
    ResetPasswordRequest,
    UserResponse,
)
from src.presentation.api.v1.auth.service import UserService

router = APIRouter(prefix="/users/me", tags=["Me"])


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        roles=user.roles,
        is_active=user.is_active,
        telegram_username=user.telegram_username,
        telegram_id=user.telegram_id,
    )


@router.get("", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _to_response(current_user)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_my_password(
    body: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> None:
    await service.reset_password(current_user.id, body.old_password, body.new_password)


@router.post("/bind-telegram", status_code=status.HTTP_204_NO_CONTENT)
async def bind_my_telegram(
    body: BindTelegramRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> None:
    await service.bind_telegram(current_user.id, body.telegram_username)
