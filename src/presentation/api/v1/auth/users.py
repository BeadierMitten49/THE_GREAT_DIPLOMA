from fastapi import APIRouter, Depends, status

from src.domain.auth.entities import User
from src.presentation.api.v1.auth.dependencies import get_user_service
from src.presentation.api.v1.auth.schemas import (
    BindTelegramRequest,
    CreateUserRequest,
    ResetPasswordRequest,
    SetRolesRequest,
    UpdateUserRequest,
    UserResponse,
)
from src.presentation.api.v1.auth.service import UserService
from src.presentation.api.v1.dependencies import director_only, director_or_warehouse

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[director_or_warehouse])


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


@router.get("", response_model=list[UserResponse])
async def get_users(
    include_inactive: bool = False,
    service: UserService = Depends(get_user_service),
):
    return [_to_response(u) for u in await service.get_all(include_inactive)]


@router.get("/{id}", response_model=UserResponse)
async def get_user(id: int, service: UserService = Depends(get_user_service)):
    return _to_response(await service.get(id))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[director_only])
async def create_user(
    body: CreateUserRequest,
    service: UserService = Depends(get_user_service),
):
    user_id = await service.create(body.full_name, body.password)
    return {"id": user_id}


@router.patch("/{id}", response_model=UserResponse, dependencies=[director_only])
async def update_user(
    id: int,
    body: UpdateUserRequest,
    service: UserService = Depends(get_user_service),
):
    await service.update(id, body.full_name)
    return _to_response(await service.get(id))


@router.post("/{id}/roles", status_code=status.HTTP_204_NO_CONTENT, dependencies=[director_only])
async def set_roles(
    id: int,
    body: SetRolesRequest,
    service: UserService = Depends(get_user_service),
):
    await service.set_roles(id, body.roles)


@router.post("/{id}/deactivate", status_code=status.HTTP_204_NO_CONTENT, dependencies=[director_only])
async def deactivate_user(id: int, service: UserService = Depends(get_user_service)):
    await service.deactivate(id)


@router.post("/{id}/activate", status_code=status.HTTP_204_NO_CONTENT, dependencies=[director_only])
async def activate_user(id: int, service: UserService = Depends(get_user_service)):
    await service.activate(id)


@router.post("/{id}/bind-telegram", status_code=status.HTTP_204_NO_CONTENT, dependencies=[director_only])
async def bind_telegram(
    id: int,
    body: BindTelegramRequest,
    service: UserService = Depends(get_user_service),
):
    await service.bind_telegram(id, body.telegram_username)


@router.post("/{id}/reset-password", status_code=status.HTTP_204_NO_CONTENT, dependencies=[director_only])
async def reset_password(
    id: int,
    body: ResetPasswordRequest,
    service: UserService = Depends(get_user_service),
):
    await service.reset_password(id, body.old_password, body.new_password)
