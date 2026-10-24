"""Independent durable ingestion worker logic; no HTTP event-loop background work."""

from __future__ import annotations

import asyncio
import hashlib

from src.infrastructure.di.inject import inject
from src.infrastructure.providers.scanner.clamav_scanner import ClamAvScanner, MalwareDetected, ScanUnavailable
from src.infrastructure.providers.storage.quarantine_storage import QuarantineStorage, StorageUnavailable
from src.infrastructure.repositories.ingestion.ingestion_repository import IngestionRepository
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class IngestionWorkerService:
    def __init__(
        self,
        ingestion_repository: IngestionRepository,
        quarantine_storage: QuarantineStorage,
        clam_av_scanner: ClamAvScanner,
        config_reader: ConfigReader,
    ):
        self._repo = ingestion_repository
        self._storage = quarantine_storage
        self._scanner = clam_av_scanner
        self._cfg = config_reader.settings.ingestion
        self._scope = config_reader.settings.deployment_zone

    async def _heartbeat_async(self, job_id, token: str, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=self._cfg.lease_seconds / 3)
            except TimeoutError:
                if not await self._repo.heartbeat_async(job_id, token, self._cfg.lease_seconds):
                    return

    async def run_once_async(self, worker_id: str) -> bool:
        claim = await self._repo.claim_async(worker_id, self._scope, self._cfg.lease_seconds)
        if claim is None:
            await self._repo.expire_staging_async(self._scope)
            return False
        job_id, token, key, expected_hash, expected_size = claim
        stop = asyncio.Event()
        heartbeat = asyncio.create_task(self._heartbeat_async(job_id, token, stop))
        ok, retriable, code = False, False, None
        try:
            if not key or expected_size is None:
                code = "invalid_storage_reference"
            else:
                contents = await self._storage.get_async(key)
                if len(contents) != expected_size or hashlib.sha256(contents).hexdigest() != expected_hash:
                    code = "integrity_mismatch"
                else:
                    await self._scanner.scan_async(contents)
                    ok = True
        except MalwareDetected:
            code = "malware_detected"
        except (StorageUnavailable, ScanUnavailable):
            code, retriable = "dependency_unavailable", True
        except Exception:
            # No exception text, file bytes, credentials or object keys in audit.
            code, retriable = "processing_failed", True
        finally:
            stop.set()
            heartbeat.cancel()
            try:
                await heartbeat
            except asyncio.CancelledError:
                pass
        await self._repo.finish_async(job_id, token, ok, code, retriable)
        return True
