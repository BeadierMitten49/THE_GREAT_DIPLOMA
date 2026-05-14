from pydantic import BaseModel, Field

from src.domain.auth.value_objects import Role


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class CreateUserRequest(BaseModel):
    full_name: str
    password: str = Field(min_length=6)


class UpdateUserRequest(BaseModel):
    full_name: str


class SetRolesRequest(BaseModel):
    roles: list[Role]


class BindTelegramRequest(BaseModel):
    telegram_username: str


class ResetPasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    roles: list[Role]
    is_active: bool
    telegram_username: str | None
    telegram_id: int | None
