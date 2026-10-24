"""Guarded migration runner; no implicit schema creation at application startup."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext  # noqa: E402
from src.infrastructure.di.bootstrap import bootstrap_di  # noqa: E402
from src.infrastructure.utils.config_reader import ConfigReader  # noqa: E402


async def _settings_async():
    container = bootstrap_di()
    reader = container.resolve(ConfigReader)
    db = container.resolve(PsqlDbContext)
    return reader.settings, await db.connection_url_async()


def main() -> None:
    parser = argparse.ArgumentParser(description="PostgreSQL versioned migrations")
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--upgrade", action="store_true", help="Upgrade to head")
    operation.add_argument("--current", action="store_true", help="Display applied revision")
    operation.add_argument("--check", action="store_true", help="Fail if ORM metadata differs")
    operation.add_argument("--downgrade-test-only", action="store_true", help="Reset disposable test schema")
    args = parser.parse_args()

    try:
        settings, url = asyncio.run(_settings_async())
        if args.downgrade_test_only and (
            settings.environment not in {"development", "integration"} or not make_url(url).database.endswith("_test")
        ):
            raise RuntimeError("Downgrade permitted only for disposable *_test databases")
        cfg = Config()
        cfg.set_main_option("script_location", str(ROOT / "src" / "infrastructure" / "alembic"))
        cfg.attributes["database_url"] = url
        cfg.attributes["database_settings"] = settings.database
        if args.upgrade:
            command.upgrade(cfg, "head")
        elif args.current:
            command.current(cfg, verbose=True)
        elif args.check:
            command.check(cfg)
        else:
            command.downgrade(cfg, "base")
    except Exception:
        raise SystemExit("PostgreSQL migration failed; inspect configuration and database state") from None


if __name__ == "__main__":
    main()
