from abc import ABC, abstractmethod

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[TEntity, TModel](ABC):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    @abstractmethod
    def _model_class(self) -> type[TModel]: ...

    @abstractmethod
    def _to_entity(self, model: TModel) -> TEntity: ...

    @abstractmethod
    def _to_values(self, entity: TEntity) -> dict: ...

    async def get_by_id(self, id: int) -> TEntity | None:
        model = await self._session.get(self._model_class, id)
        return self._to_entity(model) if model else None

    async def get_all(self, include_inactive: bool = False) -> list[TEntity]:
        stmt = select(self._model_class)
        if not include_inactive:
            stmt = stmt.where(self._model_class.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def save(self, entity: TEntity) -> int:
        values = self._to_values(entity)
        if entity.id is None:
            model = self._model_class(**values)
            self._session.add(model)
            await self._session.flush()
            entity.id = model.id
            return model.id
        else:
            await self._session.execute(
                update(self._model_class)
                .where(self._model_class.id == entity.id)
                .values(**values)
            )
            return entity.id


class BaseCatalogRepository[TEntity, TModel](BaseRepository[TEntity, TModel]):
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        stmt = select(self._model_class.id).where(self._model_class.name == name)
        if exclude_id is not None:
            stmt = stmt.where(self._model_class.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar() is not None
