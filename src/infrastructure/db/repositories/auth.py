from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.auth.entities import User
from src.domain.auth.interfaces import IUserRepository
from src.domain.auth.value_objects import Role
from src.infrastructure.db.models.auth import UserModel, UserRoleModel
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
