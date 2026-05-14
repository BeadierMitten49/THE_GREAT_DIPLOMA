import pytest

from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.infrastructure.db.repositories.auth import (
    AuthLogRepository,
    RefreshTokenRepository,
    UserCredentialRepository,
    UserRepository,
)

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(username: str = "ivanov_ivan", full_name: str = "Иванов Иван") -> User:
    return User(username=username, full_name=full_name)


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------


class TestUserRepository:
    async def test_save_and_get_by_id(self, session):
        repo = UserRepository(session)
        user = make_user()
        await repo.save(user)

        found = await repo.get_by_id(user.id)
        assert found is not None
        assert found.username == "ivanov_ivan"
        assert found.full_name == "Иванов Иван"
        assert found.is_active is True
        assert found.roles == []

    async def test_save_new_returns_id(self, session):
        repo = UserRepository(session)
        user = make_user()
        id_ = await repo.save(user)
        assert id_ == user.id
        assert id_ is not None

    async def test_get_by_id_not_found_returns_none(self, session):
        repo = UserRepository(session)
        assert await repo.get_by_id(999) is None

    async def test_get_by_username(self, session):
        repo = UserRepository(session)
        user = make_user()
        await repo.save(user)

        found = await repo.get_by_username("ivanov_ivan")
        assert found is not None
        assert found.id == user.id

    async def test_get_by_username_not_found_returns_none(self, session):
        repo = UserRepository(session)
        assert await repo.get_by_username("nobody") is None

    async def test_exists_by_username_true(self, session):
        repo = UserRepository(session)
        await repo.save(make_user())
        assert await repo.exists_by_username("ivanov_ivan") is True

    async def test_exists_by_username_false(self, session):
        repo = UserRepository(session)
        assert await repo.exists_by_username("nobody") is False

    async def test_exists_by_username_excludes_self(self, session):
        repo = UserRepository(session)
        user = make_user()
        await repo.save(user)
        assert await repo.exists_by_username("ivanov_ivan", exclude_id=user.id) is False

    async def test_get_all_returns_active_by_default(self, session):
        repo = UserRepository(session)
        active = make_user("active_user", "Активный")
        inactive = make_user("inactive_user", "Неактивный")
        inactive.deactivate()
        await repo.save(active)
        await repo.save(inactive)

        result = await repo.get_all()
        usernames = [u.username for u in result]
        assert "active_user" in usernames
        assert "inactive_user" not in usernames

    async def test_get_all_include_inactive(self, session):
        repo = UserRepository(session)
        active = make_user("active2", "Активный 2")
        inactive = make_user("inactive2", "Неактивный 2")
        inactive.deactivate()
        await repo.save(active)
        await repo.save(inactive)

        result = await repo.get_all(include_inactive=True)
        usernames = [u.username for u in result]
        assert "active2" in usernames
        assert "inactive2" in usernames

    async def test_save_updates_fields(self, session):
        repo = UserRepository(session)
        user = make_user()
        await repo.save(user)

        user.full_name = "Иванов Пётр"
        user.deactivate()
        await repo.save(user)

        found = await repo.get_by_id(user.id)
        assert found.full_name == "Иванов Пётр"
        assert found.is_active is False

    async def test_save_syncs_roles_on_add(self, session):
        repo = UserRepository(session)
        user = make_user()
        await repo.save(user)

        user.add_role(Role.director)
        user.add_role(Role.warehouse)
        await repo.save(user)

        found = await repo.get_by_id(user.id)
        assert set(found.roles) == {Role.director, Role.warehouse}

    async def test_save_syncs_roles_on_remove(self, session):
        repo = UserRepository(session)
        user = make_user()
        user.add_role(Role.director)
        user.add_role(Role.production)
        await repo.save(user)

        user.remove_role(Role.production)
        await repo.save(user)

        found = await repo.get_by_id(user.id)
        assert found.roles == [Role.director]

    async def test_telegram_fields_saved(self, session):
        repo = UserRepository(session)
        user = make_user()
        user.set_telegram_username("ivan_tg")
        user.set_telegram_id(123456789)
        await repo.save(user)

        found = await repo.get_by_id(user.id)
        assert found.telegram_username == "ivan_tg"
        assert found.telegram_id == 123456789


# ---------------------------------------------------------------------------
# UserCredentialRepository
# ---------------------------------------------------------------------------


class TestUserCredentialRepository:
    async def test_save_and_get_hashed_password(self, session):
        user_repo = UserRepository(session)
        user = make_user()
        await user_repo.save(user)

        cred_repo = UserCredentialRepository(session)
        await cred_repo.save(user.id, "hashed_pw_123")

        result = await cred_repo.get_hashed_password(user.id)
        assert result == "hashed_pw_123"

    async def test_get_hashed_password_not_found_returns_none(self, session):
        cred_repo = UserCredentialRepository(session)
        assert await cred_repo.get_hashed_password(999) is None

    async def test_update_password(self, session):
        user_repo = UserRepository(session)
        user = make_user()
        await user_repo.save(user)

        cred_repo = UserCredentialRepository(session)
        await cred_repo.save(user.id, "old_hash")
        await cred_repo.update_password(user.id, "new_hash")

        result = await cred_repo.get_hashed_password(user.id)
        assert result == "new_hash"


# ---------------------------------------------------------------------------
# RefreshTokenRepository
# ---------------------------------------------------------------------------


class TestRefreshTokenRepository:
    async def test_save_and_get_by_token(self, session):
        user_repo = UserRepository(session)
        user = make_user()
        await user_repo.save(user)

        repo = RefreshTokenRepository(session)
        await repo.save(user.id, "token-abc")

        data = await repo.get_by_token("token-abc")
        assert data is not None
        assert data.user_id == user.id

    async def test_get_by_token_not_found_returns_none(self, session):
        repo = RefreshTokenRepository(session)
        assert await repo.get_by_token("nonexistent") is None

    async def test_revoke_removes_token(self, session):
        user_repo = UserRepository(session)
        user = make_user()
        await user_repo.save(user)

        repo = RefreshTokenRepository(session)
        await repo.save(user.id, "token-to-revoke")
        await repo.revoke("token-to-revoke")

        assert await repo.get_by_token("token-to-revoke") is None

    async def test_revoke_nonexistent_does_not_raise(self, session):
        repo = RefreshTokenRepository(session)
        await repo.revoke("does-not-exist")

    async def test_revoke_all_for_user(self, session):
        user_repo = UserRepository(session)
        user = make_user()
        await user_repo.save(user)

        repo = RefreshTokenRepository(session)
        await repo.save(user.id, "token-1")
        await repo.save(user.id, "token-2")
        await repo.revoke_all_for_user(user.id)

        assert await repo.get_by_token("token-1") is None
        assert await repo.get_by_token("token-2") is None


# ---------------------------------------------------------------------------
# AuthLogRepository
# ---------------------------------------------------------------------------


class TestAuthLogRepository:
    async def test_log_failed_attempt(self, session):
        repo = AuthLogRepository(session)
        await repo.log_attempt("ivanov_ivan", None, success=False)
        count = await repo.count_failed_recent("ivanov_ivan")
        assert count == 1

    async def test_log_successful_attempt_not_counted(self, session):
        repo = AuthLogRepository(session)
        await repo.log_attempt("ivanov_ivan", None, success=True)
        assert await repo.count_failed_recent("ivanov_ivan") == 0

    async def test_count_accumulates_failures(self, session):
        repo = AuthLogRepository(session)
        for _ in range(3):
            await repo.log_attempt("ivanov_ivan", None, success=False)
        assert await repo.count_failed_recent("ivanov_ivan") == 3

    async def test_count_only_for_given_username(self, session):
        repo = AuthLogRepository(session)
        await repo.log_attempt("user_a", None, success=False)
        await repo.log_attempt("user_a", None, success=False)
        await repo.log_attempt("user_b", None, success=False)
        assert await repo.count_failed_recent("user_a") == 2
        assert await repo.count_failed_recent("user_b") == 1

    async def test_log_with_user_id(self, session):
        user_repo = UserRepository(session)
        user = make_user()
        await user_repo.save(user)

        repo = AuthLogRepository(session)
        await repo.log_attempt("ivanov_ivan", user.id, success=False)
        assert await repo.count_failed_recent("ivanov_ivan") == 1
