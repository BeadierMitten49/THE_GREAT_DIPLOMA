import pytest

from src.application.auth.exceptions import AuthenticationError, InvalidTokenError, RateLimitError
from src.application.references.exceptions import NotFoundError
from src.presentation.api.v1.auth.service import AuthService, UserService

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def make_user(session, full_name: str = "Иванов Иван", password: str = "secret123") -> int:
    svc = UserService(session)
    return await svc.create(full_name=full_name, password=password)


# ---------------------------------------------------------------------------
# UserService
# ---------------------------------------------------------------------------


class TestUserService:
    async def test_create_returns_id(self, session):
        svc = UserService(session)
        user_id = await svc.create(full_name="Иванов Иван", password="secret123")
        assert isinstance(user_id, int)

    async def test_create_generates_username(self, session):
        svc = UserService(session)
        user_id = await svc.create(full_name="Иванов Иван", password="secret123")
        user = await svc.get(user_id)
        assert user.username == "ivanov_ivan"

    async def test_create_duplicate_name_gets_suffix(self, session):
        svc = UserService(session)
        await svc.create(full_name="Иванов Иван", password="secret123")
        user_id2 = await svc.create(full_name="Иванов Иван", password="secret123")
        user2 = await svc.get(user_id2)
        assert user2.username == "ivanov_ivan_2"

    async def test_get_not_found_raises(self, session):
        svc = UserService(session)
        with pytest.raises(NotFoundError):
            await svc.get(999)

    async def test_get_all_returns_active_only_by_default(self, session):
        svc = UserService(session)
        active_id = await svc.create("Активный Алексей", "pass123")
        inactive_id = await svc.create("Неактивный Борис", "pass123")
        await svc.deactivate(inactive_id)

        users = await svc.get_all()
        usernames = [u.username for u in users]
        assert any(u.id == active_id for u in users)
        assert all(u.id != inactive_id for u in users)
        assert all(u.is_active for u in users)

    async def test_get_all_include_inactive(self, session):
        svc = UserService(session)
        active_id = await svc.create("Активный Виктор", "pass123")
        inactive_id = await svc.create("Неактивный Геннадий", "pass123")
        await svc.deactivate(inactive_id)

        users = await svc.get_all(include_inactive=True)
        ids = [u.id for u in users]
        assert active_id in ids
        assert inactive_id in ids

    async def test_update_full_name(self, session):
        svc = UserService(session)
        user_id = await make_user(session)
        await svc.update(user_id, full_name="Иванов Пётр")
        user = await svc.get(user_id)
        assert user.full_name == "Иванов Пётр"

    async def test_set_roles(self, session):
        from src.domain.auth.value_objects import Role
        svc = UserService(session)
        user_id = await make_user(session)
        await svc.set_roles(user_id, [Role.director, Role.warehouse])
        user = await svc.get(user_id)
        assert set(user.roles) == {Role.director, Role.warehouse}

    async def test_deactivate_and_activate(self, session):
        svc = UserService(session)
        user_id = await make_user(session)

        await svc.deactivate(user_id)
        assert (await svc.get(user_id)).is_active is False

        await svc.activate(user_id)
        assert (await svc.get(user_id)).is_active is True

    async def test_bind_telegram(self, session):
        svc = UserService(session)
        user_id = await make_user(session)
        await svc.bind_telegram(user_id, telegram_username="ivan_tg")
        user = await svc.get(user_id)
        assert user.telegram_username == "ivan_tg"

    async def test_reset_password_success(self, session):
        svc = UserService(session)
        user_id = await svc.create("Сидоров Сидор", "old_pass")
        await svc.reset_password(user_id, old_password="old_pass", new_password="new_pass")

    async def test_reset_password_wrong_old_raises(self, session):
        svc = UserService(session)
        user_id = await svc.create("Козлов Козёл", "real_pass")
        with pytest.raises(AuthenticationError):
            await svc.reset_password(user_id, old_password="wrong", new_password="new_pass")


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------


class TestAuthService:
    async def test_login_success_returns_tokens(self, session):
        await make_user(session, password="secret123")
        svc = AuthService(session)
        result = await svc.login("ivanov_ivan", "secret123")
        assert result.access_token
        assert result.refresh_token

    async def test_login_wrong_password_raises(self, session):
        await make_user(session, password="secret123")
        svc = AuthService(session)
        with pytest.raises(AuthenticationError):
            await svc.login("ivanov_ivan", "wrong")

    async def test_login_unknown_user_raises(self, session):
        svc = AuthService(session)
        with pytest.raises(AuthenticationError):
            await svc.login("nobody", "secret123")

    async def test_login_inactive_user_raises(self, session):
        user_id = await make_user(session, password="secret123")
        user_svc = UserService(session)
        await user_svc.deactivate(user_id)

        auth_svc = AuthService(session)
        with pytest.raises(AuthenticationError):
            await auth_svc.login("ivanov_ivan", "secret123")

    async def test_login_rate_limited_after_5_failures(self, session):
        await make_user(session, password="secret123")
        svc = AuthService(session)
        for _ in range(5):
            with pytest.raises(AuthenticationError):
                await svc.login("ivanov_ivan", "wrong")
        with pytest.raises(RateLimitError):
            await svc.login("ivanov_ivan", "secret123")

    async def test_refresh_tokens_success(self, session):
        await make_user(session, password="secret123")
        auth_svc = AuthService(session)
        tokens = await auth_svc.login("ivanov_ivan", "secret123")
        new_tokens = await auth_svc.refresh_tokens(tokens.refresh_token)
        assert new_tokens.access_token
        assert new_tokens.refresh_token != tokens.refresh_token

    async def test_refresh_tokens_old_token_revoked(self, session):
        await make_user(session, password="secret123")
        auth_svc = AuthService(session)
        tokens = await auth_svc.login("ivanov_ivan", "secret123")
        await auth_svc.refresh_tokens(tokens.refresh_token)
        with pytest.raises(InvalidTokenError):
            await auth_svc.refresh_tokens(tokens.refresh_token)

    async def test_refresh_tokens_invalid_raises(self, session):
        svc = AuthService(session)
        with pytest.raises(InvalidTokenError):
            await svc.refresh_tokens("nonexistent-token")

    async def test_logout_revokes_token(self, session):
        await make_user(session, password="secret123")
        auth_svc = AuthService(session)
        tokens = await auth_svc.login("ivanov_ivan", "secret123")
        await auth_svc.logout(tokens.refresh_token)
        with pytest.raises(InvalidTokenError):
            await auth_svc.refresh_tokens(tokens.refresh_token)
