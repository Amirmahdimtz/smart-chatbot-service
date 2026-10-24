"""Alembic online-only migration environment with a PostgreSQL advisory lock."""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.infrastructure.context.sql_db.psql_dbcontext import Base, connection_options
from src.infrastructure.models import entities  # noqa: F401 - explicit metadata registration

config = context.config
target_metadata = Base.metadata
_LOCK_KEY = 850303


def _run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        transactional_ddl=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_online_async() -> None:
    url = config.attributes["database_url"]
    settings = config.attributes["database_settings"]
    engine = create_async_engine(url, **connection_options(settings))
    try:
        async with engine.connect() as connection:
            locked = await connection.scalar(text(f"SELECT pg_try_advisory_lock({_LOCK_KEY})"))
            await connection.commit()
            if not locked:
                raise RuntimeError("Another database migration is already running")
            try:
                await connection.run_sync(_run_migrations)
            finally:
                if connection.in_transaction():
                    await connection.rollback()
                await connection.execute(text(f"SELECT pg_advisory_unlock({_LOCK_KEY})"))
                await connection.commit()
    finally:
        await engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Offline migrations are disabled; use the guarded migration runner")
asyncio.run(_run_online_async())
