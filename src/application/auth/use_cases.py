import uuid

from src.application.auth.dto import (
    BindTelegramDTO,
    CreateUserDTO,
    LoginDTO,
    ResetPasswordDTO,
    SetUserRolesDTO,
    TokenPairDTO,
    UpdateUserDTO,
)
from src.application.auth.exceptions import AuthenticationError, DeactivatedUserError, InvalidTokenError, RateLimitError
from src.application.ports.auth import (
    IAuthLogRepository,
    IJWTService,
    IPasswordHasher,
    IRefreshTokenRepository,
    IUserCredentialRepository,
)
from src.application.references.exceptions import NotFoundError
from src.domain.auth.entities import User
from src.domain.auth.interfaces import IUserRepository
from src.domain.auth.value_objects import Role

_TRANSLIT: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

_RATE_LIMIT_MAX_ATTEMPTS = 5
_RATE_LIMIT_WINDOW_SECONDS = 1800  # 30 minutes


def _translit(text: str) -> str:
    return "".join(_TRANSLIT.get(ch, ch) for ch in text.lower())


async def generate_username(full_name: str, user_repo: IUserRepository) -> str:
    parts = full_name.strip().split()
    base = _translit(parts[0])
    if len(parts) > 1:
        base += "_" + _translit(parts[1])

    username = base
    suffix = 2
    while await user_repo.exists_by_username(username):
        username = f"{base}_{suffix}"
        suffix += 1
    return username


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


async def create_user(
    dto: CreateUserDTO,
    user_repo: IUserRepository,
    cred_repo: IUserCredentialRepository,
    hasher: IPasswordHasher,
) -> int:
    username = await generate_username(dto.full_name, user_repo)
    user = User(username=username, full_name=dto.full_name)
    user_id = await user_repo.save(user)
    await cred_repo.save(user_id, hasher.hash(dto.password))
    return user_id


async def get_user(id: int, user_repo: IUserRepository) -> User:
    user = await user_repo.get_by_id(id)
    if user is None:
        raise NotFoundError("User", id)
    return user


async def get_users(
    user_repo: IUserRepository,
    include_inactive: bool = False,
) -> list[User]:
    return await user_repo.get_all(include_inactive=include_inactive)


async def update_user(id: int, dto: UpdateUserDTO, user_repo: IUserRepository) -> None:
    user = await get_user(id, user_repo)
    user.full_name = dto.full_name
    await user_repo.save(user)


async def set_user_roles(
    id: int,
    dto: SetUserRolesDTO,
    user_repo: IUserRepository,
) -> None:
    user = await get_user(id, user_repo)
    current = set(user.roles)
    desired = set(dto.roles)

    for role in desired - current:
        user.add_role(role)
    for role in current - desired:
        user.remove_role(role)

    await user_repo.save(user)


async def deactivate_user(id: int, user_repo: IUserRepository) -> None:
    user = await get_user(id, user_repo)
    user.deactivate()
    await user_repo.save(user)


async def activate_user(id: int, user_repo: IUserRepository) -> None:
    user = await get_user(id, user_repo)
    user.activate()
    await user_repo.save(user)


async def bind_telegram(
    user_id: int,
    dto: BindTelegramDTO,
    user_repo: IUserRepository,
) -> None:
    user = await get_user(user_id, user_repo)
    user.set_telegram_username(dto.telegram_username)
    await user_repo.save(user)


async def reset_password(
    user_id: int,
    dto: ResetPasswordDTO,
    cred_repo: IUserCredentialRepository,
    hasher: IPasswordHasher,
) -> None:
    hashed = await cred_repo.get_hashed_password(user_id)
    if hashed is None or not hasher.verify(dto.old_password, hashed):
        raise AuthenticationError("current password is incorrect")
    await cred_repo.update_password(user_id, hasher.hash(dto.new_password))


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def login(
    dto: LoginDTO,
    user_repo: IUserRepository,
    cred_repo: IUserCredentialRepository,
    auth_log_repo: IAuthLogRepository,
    hasher: IPasswordHasher,
    jwt_service: IJWTService,
    token_repo: IRefreshTokenRepository,
) -> TokenPairDTO:
    failed_count = await auth_log_repo.count_failed_recent(
        dto.username, _RATE_LIMIT_WINDOW_SECONDS
    )
    if failed_count >= _RATE_LIMIT_MAX_ATTEMPTS:
        raise RateLimitError(dto.username)

    user = await user_repo.get_by_username(dto.username)

    if user is None:
        await auth_log_repo.log_attempt(dto.username, None, success=False)
        raise AuthenticationError()

    if not user.is_active:
        await auth_log_repo.log_attempt(dto.username, user.id, success=False)
        raise DeactivatedUserError()

    hashed = await cred_repo.get_hashed_password(user.id)
    if hashed is None or not hasher.verify(dto.password, hashed):
        await auth_log_repo.log_attempt(dto.username, user.id, success=False)
        raise AuthenticationError()

    await auth_log_repo.log_attempt(dto.username, user.id, success=True)

    access_token = jwt_service.create_access_token(
        user_id=user.id,
        roles=[r.value for r in user.roles],
    )
    refresh_token = str(uuid.uuid4())
    await token_repo.save(user.id, refresh_token)

    return TokenPairDTO(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(
    refresh_token: str,
    token_repo: IRefreshTokenRepository,
    user_repo: IUserRepository,
    jwt_service: IJWTService,
) -> TokenPairDTO:
    token_data = await token_repo.get_by_token(refresh_token)
    if token_data is None:
        raise InvalidTokenError()

    user = await user_repo.get_by_id(token_data.user_id)
    if user is None or not user.is_active:
        await token_repo.revoke(refresh_token)
        raise InvalidTokenError("user not found or deactivated")

    await token_repo.revoke(refresh_token)

    access_token = jwt_service.create_access_token(
        user_id=user.id,
        roles=[r.value for r in user.roles],
    )
    new_refresh_token = str(uuid.uuid4())
    await token_repo.save(user.id, new_refresh_token)

    return TokenPairDTO(access_token=access_token, refresh_token=new_refresh_token)


async def logout(
    refresh_token: str,
    token_repo: IRefreshTokenRepository,
) -> None:
    await token_repo.revoke(refresh_token)
