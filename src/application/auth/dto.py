from dataclasses import dataclass

from src.domain.auth.value_objects import Role


@dataclass(frozen=True)
class CreateUserDTO:
    full_name: str
    password: str


@dataclass(frozen=True)
class LoginDTO:
    username: str
    password: str


@dataclass(frozen=True)
class TokenPairDTO:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class UpdateUserDTO:
    full_name: str


@dataclass(frozen=True)
class SetUserRolesDTO:
    roles: list[Role]


@dataclass(frozen=True)
class BindTelegramDTO:
    telegram_username: str


@dataclass(frozen=True)
class ResetPasswordDTO:
    old_password: str
    new_password: str
