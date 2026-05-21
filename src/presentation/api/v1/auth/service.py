from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth.dto import (
    BindTelegramDTO,
    CreateUserDTO,
    LoginDTO,
    ResetPasswordDTO,
    SetUserRolesDTO,
    TokenPairDTO,
    UpdateUserDTO,
)
from src.application.auth.use_cases import (
    activate_user,
    bind_telegram,
    create_user,
    deactivate_user,
    get_user,
    get_users,
    login,
    logout,
    refresh_tokens,
    reset_password,
    set_user_roles,
    update_user,
)
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.infrastructure.db.repositories.auth import (
    AuthLogRepository,
    RefreshTokenRepository,
    UserCredentialRepository,
    UserRepository,
)
from src.infrastructure.security.jwt_service import JWTService
from src.infrastructure.security.password_hasher import BcryptPasswordHasher


class AuthService:
    def __init__(self, session: AsyncSession, log_session: AsyncSession) -> None:
        self._user_repo = UserRepository(session)
        self._cred_repo = UserCredentialRepository(session)
        self._token_repo = RefreshTokenRepository(session)
        self._auth_log_repo = AuthLogRepository(log_session)
        self._hasher = BcryptPasswordHasher()
        self._jwt = JWTService()

    async def login(self, username: str, password: str) -> TokenPairDTO:
        return await login(
            LoginDTO(username=username, password=password),
            self._user_repo,
            self._cred_repo,
            self._auth_log_repo,
            self._hasher,
            self._jwt,
            self._token_repo,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenPairDTO:
        return await refresh_tokens(
            refresh_token,
            self._token_repo,
            self._user_repo,
            self._jwt,
        )

    async def logout(self, refresh_token: str) -> None:
        await logout(refresh_token, self._token_repo)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._user_repo = UserRepository(session)
        self._cred_repo = UserCredentialRepository(session)
        self._hasher = BcryptPasswordHasher()

    async def create(self, full_name: str, password: str) -> int:
        return await create_user(
            CreateUserDTO(full_name=full_name, password=password),
            self._user_repo,
            self._cred_repo,
            self._hasher,
        )

    async def get(self, id: int) -> User:
        return await get_user(id, self._user_repo)

    async def get_all(self, include_inactive: bool = False) -> list[User]:
        return await get_users(self._user_repo, include_inactive)

    async def update(self, id: int, full_name: str) -> None:
        await update_user(id, UpdateUserDTO(full_name=full_name), self._user_repo)

    async def set_roles(self, id: int, roles: list[Role]) -> None:
        await set_user_roles(id, SetUserRolesDTO(roles=roles), self._user_repo)

    async def deactivate(self, id: int) -> None:
        await deactivate_user(id, self._user_repo)

    async def activate(self, id: int) -> None:
        await activate_user(id, self._user_repo)

    async def bind_telegram(self, id: int, telegram_username: str) -> None:
        await bind_telegram(id, BindTelegramDTO(telegram_username=telegram_username), self._user_repo)

    async def reset_password(self, id: int, old_password: str, new_password: str) -> None:
        await reset_password(
            id,
            ResetPasswordDTO(old_password=old_password, new_password=new_password),
            self._cred_repo,
            self._hasher,
        )
