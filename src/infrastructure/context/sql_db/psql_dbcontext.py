"""PostgreSQL engine lifecycle and explicit per-operation transaction boundaries."""

from __future__ import annotations

import ssl
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.context.vault.vault_service import VaultService
from src.infrastructure.di.inject import inject
from src.infrastructure.utils.config_reader import ConfigReader, DatabaseSettings


class Base(DeclarativeBase):
    pass


class DatabaseUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("PostgreSQL unavailable or incorrectly configured")


def connection_options(settings: DatabaseSettings) -> dict:
    ssl_option = (
        ssl.create_default_context(cafile=settings.tls_ca_file) if settings.tls_mode == "verify-full" else False
    )
    return {
        "pool_size": settings.pool_size,
        "max_overflow": settings.max_overflow,
        "pool_timeout": settings.pool_timeout_seconds,
        "pool_pre_ping": True,
        "hide_parameters": True,
        "connect_args": {
            "ssl": ssl_option,
            "timeout": settings.connect_timeout_seconds,
            "server_settings": {"statement_timeout": str(settings.statement_timeout_ms)},
        },
    }


def validate_database_url(url: str) -> str:
    try:
        parsed = make_url(url)
        if (
            parsed.drivername != "postgresql+asyncpg"
            or not parsed.host
            or not parsed.database
            or not parsed.username
            or parsed.password is None
            or parsed.query
            or (parsed.port is not None and not 1 <= parsed.port <= 65535)
        ):
            raise ValueError("Invalid driver/URL")
    except (ValueError, TypeError, AttributeError, ArgumentError):
        raise DatabaseUnavailable() from None
    return url


@inject
class PsqlDbContext:
    __di_singleton__ = True

    def __init__(self, config_reader: ConfigReader, vault_service: VaultService):
        self._cfg = config_reader.settings.database
        self._vault = vault_service
        self._engine: AsyncEngine | None = None
        self._factory: async_sessionmaker[AsyncSession] | None = None

    async def connection_url_async(self) -> str:
        if not self._cfg.enabled:
            raise DatabaseUnavailable()
        url = self._cfg.url
        if self._cfg.vault_secret_path:
            try:
                secret = await self._vault.read_secret_async(self._cfg.vault_secret_path)
                url = secret.get("url")
            except Exception:
                raise DatabaseUnavailable() from None
        if not isinstance(url, str):
            raise DatabaseUnavailable()
        return validate_database_url(url)

    async def start_async(self) -> None:
        if self._engine is not None:
            return
        url = await self.connection_url_async()
        engine: AsyncEngine | None = None
        try:
            engine = create_async_engine(url, **connection_options(self._cfg))
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
                # Require exactly the version currently shipped in this source tree.
                # Do not hardcode a phase's revision or silently migrate on startup.
                cfg = Config()
                migrations = Path(__file__).resolve().parents[2] / "alembic"
                cfg.set_main_option("script_location", str(migrations))
                expected = ScriptDirectory.from_config(cfg).get_current_head()
                if revision != expected:
                    raise DatabaseUnavailable()
        except Exception:
            if engine is not None:
                await engine.dispose()
            raise DatabaseUnavailable() from None
        self._engine = engine
        self._factory = async_sessionmaker(engine, expire_on_commit=False)

    async def close_async(self) -> None:
        engine, self._engine = self._engine, None
        self._factory = None
        if engine is not None:
            await engine.dispose()

    def session(self) -> AsyncSession:
        if self._factory is None:
            raise DatabaseUnavailable()
        return self._factory()

    @asynccontextmanager
    async def transaction_async(self):
        async with self.session() as session:
            async with session.begin():
                yield session
