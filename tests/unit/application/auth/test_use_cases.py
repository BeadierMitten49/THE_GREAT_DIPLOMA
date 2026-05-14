import pytest

from src.application.auth.dto import (
    BindTelegramDTO,
    CreateUserDTO,
    LoginDTO,
    ResetPasswordDTO,
    SetUserRolesDTO,
    UpdateUserDTO,
)
from src.application.auth.exceptions import AuthenticationError, InvalidTokenError, RateLimitError
from src.application.auth.use_cases import (
    activate_user,
    bind_telegram,
    create_user,
    deactivate_user,
    generate_username,
    get_user,
    get_users,
    login,
    logout,
    refresh_tokens,
    reset_password,
    set_user_roles,
    update_user,
)
from src.application.references.exceptions import NotFoundError
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role

from .conftest import FakeAuthLogRepository


# ---------------------------------------------------------------------------
# generate_username
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_username_simple(user_repo):
    username = await generate_username("Иван Петров", user_repo)
    assert username == "ivan_petrov"


@pytest.mark.asyncio
async def test_generate_username_collision(user_repo):
    existing = User(username="ivan_petrov", full_name="Иван Петров")
    await user_repo.save(existing)

    username = await generate_username("Иван Петров", user_repo)
    assert username == "ivan_petrov_2"


@pytest.mark.asyncio
async def test_generate_username_multiple_collisions(user_repo):
    for name in ["ivan_petrov", "ivan_petrov_2"]:
        await user_repo.save(User(username=name, full_name="X"))

    username = await generate_username("Иван Петров", user_repo)
    assert username == "ivan_petrov_3"


@pytest.mark.asyncio
async def test_generate_username_single_word(user_repo):
    username = await generate_username("Мария", user_repo)
    assert username == "mariya"


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user_returns_id(user_repo, cred_repo, hasher):
    dto = CreateUserDTO(full_name="Анна Сидорова", password="pass123")
    user_id = await create_user(dto, user_repo, cred_repo, hasher)
    assert user_id == 1


@pytest.mark.asyncio
async def test_create_user_saves_hashed_password(user_repo, cred_repo, hasher):
    dto = CreateUserDTO(full_name="Анна Сидорова", password="pass123")
    user_id = await create_user(dto, user_repo, cred_repo, hasher)
    assert await cred_repo.get_hashed_password(user_id) == "hashed:pass123"


@pytest.mark.asyncio
async def test_create_user_generates_username(user_repo, cred_repo, hasher):
    dto = CreateUserDTO(full_name="Анна Сидорова", password="pass123")
    user_id = await create_user(dto, user_repo, cred_repo, hasher)
    user = await user_repo.get_by_id(user_id)
    assert user.username == "anna_sidorova"


# ---------------------------------------------------------------------------
# get_user / get_users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_found(user_repo, saved_user):
    user = await get_user(saved_user.id, user_repo)
    assert user.id == saved_user.id


@pytest.mark.asyncio
async def test_get_user_not_found(user_repo):
    with pytest.raises(NotFoundError):
        await get_user(999, user_repo)


@pytest.mark.asyncio
async def test_get_users_active_only(user_repo, saved_user):
    inactive = User(username="old_user", full_name="Старый Пользователь")
    await user_repo.save(inactive)
    inactive.deactivate()
    await user_repo.save(inactive)

    users = await get_users(user_repo, include_inactive=False)
    assert all(u.is_active for u in users)
    assert len(users) == 1


@pytest.mark.asyncio
async def test_get_users_include_inactive(user_repo, saved_user):
    inactive = User(username="old_user", full_name="Старый Пользователь")
    await user_repo.save(inactive)
    inactive.deactivate()
    await user_repo.save(inactive)

    users = await get_users(user_repo, include_inactive=True)
    assert len(users) == 2


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_user_changes_full_name(user_repo, saved_user):
    dto = UpdateUserDTO(full_name="Иван Сидоров")
    await update_user(saved_user.id, dto, user_repo)
    user = await user_repo.get_by_id(saved_user.id)
    assert user.full_name == "Иван Сидоров"


@pytest.mark.asyncio
async def test_update_user_not_found(user_repo):
    with pytest.raises(NotFoundError):
        await update_user(999, UpdateUserDTO(full_name="X"), user_repo)


# ---------------------------------------------------------------------------
# set_user_roles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_user_roles_adds_roles(user_repo, saved_user):
    dto = SetUserRolesDTO(roles=[Role.director, Role.warehouse])
    await set_user_roles(saved_user.id, dto, user_repo)
    user = await user_repo.get_by_id(saved_user.id)
    assert Role.warehouse in user.roles


@pytest.mark.asyncio
async def test_set_user_roles_removes_old_roles(user_repo, saved_user):
    dto = SetUserRolesDTO(roles=[Role.warehouse])
    await set_user_roles(saved_user.id, dto, user_repo)
    user = await user_repo.get_by_id(saved_user.id)
    assert Role.director not in user.roles
    assert Role.warehouse in user.roles


@pytest.mark.asyncio
async def test_set_user_roles_empty_clears_all(user_repo, saved_user):
    dto = SetUserRolesDTO(roles=[])
    await set_user_roles(saved_user.id, dto, user_repo)
    user = await user_repo.get_by_id(saved_user.id)
    assert user.roles == []


# ---------------------------------------------------------------------------
# deactivate_user / activate_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deactivate_user(user_repo, saved_user):
    await deactivate_user(saved_user.id, user_repo)
    user = await user_repo.get_by_id(saved_user.id)
    assert not user.is_active


@pytest.mark.asyncio
async def test_activate_user(user_repo, saved_user):
    saved_user.deactivate()
    await user_repo.save(saved_user)

    await activate_user(saved_user.id, user_repo)
    user = await user_repo.get_by_id(saved_user.id)
    assert user.is_active


# ---------------------------------------------------------------------------
# bind_telegram
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bind_telegram_sets_username(user_repo, saved_user):
    dto = BindTelegramDTO(telegram_username="ivan_tg")
    await bind_telegram(saved_user.id, dto, user_repo)
    user = await user_repo.get_by_id(saved_user.id)
    assert user.telegram_username == "ivan_tg"


@pytest.mark.asyncio
async def test_bind_telegram_user_not_found(user_repo):
    with pytest.raises(NotFoundError):
        await bind_telegram(999, BindTelegramDTO(telegram_username="x"), user_repo)


# ---------------------------------------------------------------------------
# reset_password
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reset_password_success(cred_repo, hasher, saved_user):
    dto = ResetPasswordDTO(old_password="secret", new_password="newsecret")
    await reset_password(saved_user.id, dto, cred_repo, hasher)
    assert await cred_repo.get_hashed_password(saved_user.id) == "hashed:newsecret"


@pytest.mark.asyncio
async def test_reset_password_wrong_old_password(cred_repo, hasher, saved_user):
    dto = ResetPasswordDTO(old_password="wrong", new_password="newsecret")
    with pytest.raises(AuthenticationError):
        await reset_password(saved_user.id, dto, cred_repo, hasher)


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo, saved_user):
    dto = LoginDTO(username="ivan_petrov", password="secret")
    result = await login(dto, user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo)
    assert result.access_token.startswith("token:")
    assert result.refresh_token


@pytest.mark.asyncio
async def test_login_saves_refresh_token(user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo, saved_user):
    dto = LoginDTO(username="ivan_petrov", password="secret")
    result = await login(dto, user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo)
    data = await token_repo.get_by_token(result.refresh_token)
    assert data is not None
    assert data.user_id == saved_user.id


@pytest.mark.asyncio
async def test_login_wrong_password_raises(user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo, saved_user):
    dto = LoginDTO(username="ivan_petrov", password="wrong")
    with pytest.raises(AuthenticationError):
        await login(dto, user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo)


@pytest.mark.asyncio
async def test_login_unknown_user_raises(user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo):
    dto = LoginDTO(username="nobody", password="x")
    with pytest.raises(AuthenticationError):
        await login(dto, user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo)


@pytest.mark.asyncio
async def test_login_deactivated_user_raises(user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo, saved_user):
    saved_user.deactivate()
    await user_repo.save(saved_user)

    dto = LoginDTO(username="ivan_petrov", password="secret")
    with pytest.raises(AuthenticationError):
        await login(dto, user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo)


@pytest.mark.asyncio
async def test_login_rate_limited(user_repo, cred_repo, hasher, jwt_svc, token_repo, saved_user):
    blocked_log = FakeAuthLogRepository(failed_count=5)
    dto = LoginDTO(username="ivan_petrov", password="secret")
    with pytest.raises(RateLimitError):
        await login(dto, user_repo, cred_repo, blocked_log, hasher, jwt_svc, token_repo)


@pytest.mark.asyncio
async def test_login_logs_success(user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo, saved_user):
    dto = LoginDTO(username="ivan_petrov", password="secret")
    await login(dto, user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo)
    assert any(success for _, _, success in auth_log_repo.logged)


@pytest.mark.asyncio
async def test_login_logs_failure(user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo, saved_user):
    dto = LoginDTO(username="ivan_petrov", password="wrong")
    with pytest.raises(AuthenticationError):
        await login(dto, user_repo, cred_repo, auth_log_repo, hasher, jwt_svc, token_repo)
    assert any(not success for _, _, success in auth_log_repo.logged)


# ---------------------------------------------------------------------------
# refresh_tokens
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_tokens_issues_new_pair(user_repo, token_repo, jwt_svc, saved_user):
    await token_repo.save(saved_user.id, "old-token")
    result = await refresh_tokens("old-token", token_repo, user_repo, jwt_svc)
    assert result.access_token.startswith("token:")
    assert result.refresh_token != "old-token"


@pytest.mark.asyncio
async def test_refresh_tokens_revokes_old_token(user_repo, token_repo, jwt_svc, saved_user):
    await token_repo.save(saved_user.id, "old-token")
    await refresh_tokens("old-token", token_repo, user_repo, jwt_svc)
    assert await token_repo.get_by_token("old-token") is None


@pytest.mark.asyncio
async def test_refresh_tokens_invalid_token_raises(user_repo, token_repo, jwt_svc):
    with pytest.raises(InvalidTokenError):
        await refresh_tokens("nonexistent", token_repo, user_repo, jwt_svc)


@pytest.mark.asyncio
async def test_refresh_tokens_deactivated_user_raises(user_repo, token_repo, jwt_svc, saved_user):
    await token_repo.save(saved_user.id, "old-token")
    saved_user.deactivate()
    await user_repo.save(saved_user)

    with pytest.raises(InvalidTokenError):
        await refresh_tokens("old-token", token_repo, user_repo, jwt_svc)


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logout_revokes_token(token_repo, saved_user):
    await token_repo.save(saved_user.id, "some-token")
    await logout("some-token", token_repo)
    assert await token_repo.get_by_token("some-token") is None


@pytest.mark.asyncio
async def test_logout_unknown_token_is_noop(token_repo):
    await logout("nonexistent", token_repo)  # should not raise
