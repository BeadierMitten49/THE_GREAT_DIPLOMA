from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.ports.auth import IAuthLogRepository, IRefreshTokenRepository, IUserCredentialRepository, RefreshTokenData
from src.domain.auth.entities import User
from src.domain.auth.interfaces import IUserRepository
from src.domain.auth.value_objects import Role
from src.infrastructure.db.models.auth import AuthLogModel, RefreshTokenModel, UserCredentialModel, UserModel, UserRoleModel
from src.infrastructure.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserModel], IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[UserModel]:
        return UserModel

    def _to_entity(self, model: UserModel) -> User:
        return User(
            username=model.username,
            full_name=model.full_name,
            roles=[Role(r.role) for r in model.roles],
            is_active=model.is_active,
            telegram_username=model.telegram_username,
            telegram_id=model.telegram_id,
            id=model.id,
        )

    def _to_values(self, user: User) -> dict:
        return {
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "telegram_username": user.telegram_username,
            "telegram_id": user.telegram_id,
        }

    def _with_roles(self, stmt):
        return stmt.options(selectinload(UserModel.roles))

    async def get_by_id(self, id: int) -> User | None:
        stmt = self._with_roles(select(UserModel).where(UserModel.id == id))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all(self, include_inactive: bool = False) -> list[User]:
        stmt = self._with_roles(select(UserModel))
        if not include_inactive:
            stmt = stmt.where(UserModel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_username(self, username: str) -> User | None:
        stmt = self._with_roles(select(UserModel).where(UserModel.username == username))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists_by_username(self, username: str, exclude_id: int | None = None) -> bool:
        stmt = select(UserModel.id).where(UserModel.username == username)
        if exclude_id is not None:
            stmt = stmt.where(UserModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar() is not None

    async def save(self, user: User) -> int:
        await super().save(user)
        await self._sync_roles(user.id, user.roles)
        return user.id

    async def _sync_roles(self, user_id: int, roles: list[Role]) -> None:
        current_roles = {r.value for r in roles}

        result = await self._session.execute(
            select(UserRoleModel).where(UserRoleModel.user_id == user_id)
        )
        existing = {r.role for r in result.scalars().all()}

        to_delete = existing - current_roles
        to_add = current_roles - existing

        if to_delete:
            await self._session.execute(
                delete(UserRoleModel).where(
                    UserRoleModel.user_id == user_id,
                    UserRoleModel.role.in_(to_delete),
                )
            )

        for role in to_add:
            self._session.add(UserRoleModel(user_id=user_id, role=role))

        await self._session.flush()


class UserCredentialRepository(IUserCredentialRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_hashed_password(self, user_id: int) -> str | None:
        model = await self._session.get(UserCredentialModel, user_id)
        return model.hashed_password if model else None

    async def save(self, user_id: int, hashed_password: str) -> None:
        self._session.add(UserCredentialModel(user_id=user_id, hashed_password=hashed_password))
        await self._session.flush()

    async def update_password(self, user_id: int, hashed_password: str) -> None:
        await self._session.execute(
            update(UserCredentialModel)
            .where(UserCredentialModel.user_id == user_id)
            .values(hashed_password=hashed_password)
        )
        await self._session.flush()


class RefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user_id: int, token: str) -> None:
        self._session.add(RefreshTokenModel(user_id=user_id, token=token))
        await self._session.flush()

    async def get_by_token(self, token: str) -> RefreshTokenData | None:
        model = await self._session.scalar(
            select(RefreshTokenModel).where(RefreshTokenModel.token == token)
        )
        return RefreshTokenData(user_id=model.user_id) if model else None

    async def revoke(self, token: str) -> None:
        await self._session.execute(
            delete(RefreshTokenModel).where(RefreshTokenModel.token == token)
        )
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self._session.execute(
            delete(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
        )
        await self._session.flush()


class AuthLogRepository(IAuthLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_attempt(
        self,
        username_attempt: str,
        user_id: int | None,
        success: bool,
    ) -> None:
        self._session.add(
            AuthLogModel(username_attempt=username_attempt, user_id=user_id, success=success)
        )
        await self._session.flush()

    async def count_failed_recent(self, username: str, window_seconds: int = 1800) -> int:
        since = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        result = await self._session.scalar(
            select(func.count(AuthLogModel.id)).where(
                AuthLogModel.username_attempt == username,
                AuthLogModel.success.is_(False),
                AuthLogModel.created_at >= since,
            )
        )
        return result or 0
