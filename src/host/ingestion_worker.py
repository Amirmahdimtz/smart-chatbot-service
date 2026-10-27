"""Dedicated Phase 05 worker composition root.

Run: python -m src.host.ingestion_worker
"""

from __future__ import annotations

import asyncio
import os
import signal
import socket

from src.core.services.ingestion.ingestion_worker_service import IngestionWorkerService
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.providers.storage.quarantine_storage import QuarantineStorage
from src.infrastructure.utils.config_reader import ConfigReader


async def main_async() -> None:
    container = bootstrap_di()
    settings = container.resolve(ConfigReader).settings
    if not settings.ingestion.enabled or settings.deployment_zone != "internal":
        raise RuntimeError("Synthetic ingestion worker is not enabled")
    db = container.resolve(PsqlDbContext)
    storage = container.resolve(QuarantineStorage)
    worker = container.resolve(IngestionWorkerService)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, stop.set)
        except NotImplementedError:
            pass

    worker_id = f"{socket.gethostname()[:32]}-{os.getpid()}"
    await db.start_async()
    try:
        await storage.start_async()
        try:
            while not stop.is_set():
                try:
                    had_job = await worker.run_once_async(worker_id)
                except Exception:
                    # Generic error boundary: never log arbitrary object/content/secret data.
                    had_job = False
                if not had_job:
                    try:
                        await asyncio.wait_for(stop.wait(), timeout=2)
                    except TimeoutError:
                        pass
        finally:
            await storage.close_async()
    finally:
        await db.close_async()


if __name__ == "__main__":
    asyncio.run(main_async())
