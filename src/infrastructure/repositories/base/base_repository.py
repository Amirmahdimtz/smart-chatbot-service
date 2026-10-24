"""Generic persistence primitives; caller-owned sessions are never committed here."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.context.sql_db.psql_dbcontext import Base, PsqlDbContext

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, db_context: PsqlDbContext, model: type[T]):
        self._db = db_context
        self._model = model

    @asynccontextmanager
    async def _work_async(self, session: AsyncSession | None):
        if session is not None:
            yield session
        else:
            async with self._db.transaction_async() as owned:
                yield owned

    async def insert_async(self, entity: T, *, session: AsyncSession | None = None) -> T:
        async with self._work_async(session) as current:
            current.add(entity)
            await current.flush()
            await current.refresh(entity)
        return entity

    async def insert_and_get_id_async(self, entity: T, *, session: AsyncSession | None = None):
        return (await self.insert_async(entity, session=session)).id

    async def get_by_id_async(self, entity_id, *, session: AsyncSession | None = None) -> T | None:
        async with self._work_async(session) as current:
            return await current.get(self._model, entity_id)

    async def get_all_async(self, *, session: AsyncSession | None = None) -> list[T]:
        async with self._work_async(session) as current:
            result = await current.scalars(select(self._model))
            return list(result.all())

    async def update_async(self, entity: T, *, session: AsyncSession | None = None) -> T:
        async with self._work_async(session) as current:
            merged = await current.merge(entity)
            await current.flush()
            await current.refresh(merged)
        return merged

    async def delete_async(self, entity_id, *, session: AsyncSession | None = None) -> bool:
        async with self._work_async(session) as current:
            found = await current.get(self._model, entity_id)
            if found is None:
                return False
            await current.delete(found)
            await current.flush()
            return True
