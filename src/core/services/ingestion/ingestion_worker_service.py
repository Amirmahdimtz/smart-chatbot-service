"""Independent durable ingestion worker logic; no HTTP event-loop background work."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta

from src.core.services.persian_text.persian_processing import ProcessingRejected, chunk_pages
from src.infrastructure.di.inject import inject
from src.infrastructure.providers.document.document_extractor import DocumentExtractor
from src.infrastructure.providers.scanner.clamav_scanner import ClamAvScanner, MalwareDetected, ScanUnavailable
from src.infrastructure.providers.storage.quarantine_storage import (
    QuarantineStorage,
    StorageMissing,
    StorageUnavailable,
)
from src.infrastructure.repositories.ingestion.ingestion_repository import IngestionRepository
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class IngestionWorkerService:
    def __init__(
        self,
        ingestion_repository: IngestionRepository,
        quarantine_storage: QuarantineStorage,
        clam_av_scanner: ClamAvScanner,
        document_extractor: DocumentExtractor,
        config_reader: ConfigReader,
    ):
        self._repo = ingestion_repository
        self._storage = quarantine_storage
        self._scanner = clam_av_scanner
        self._extractor = document_extractor
        self._processing = config_reader.settings.processing
        self._cfg = config_reader.settings.ingestion
        self._scope = config_reader.settings.deployment_zone

    async def _heartbeat_async(self, job_id, token: str, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=self._cfg.lease_seconds / 3)
            except TimeoutError:
                if not await self._repo.heartbeat_async(job_id, token, self._cfg.lease_seconds):
                    return

    async def _recover_staging_async(self) -> bool:
        """Recover committed quarantine objects after a crash before queue acknowledgment."""
        progressed = bool(await self._repo.exhaust_expired_async(self._scope))
        for job_id, owner, checksum, created_at, key, expected_size in await self._repo.list_stale_staging_async(
            self._scope
        ):
            if not key or expected_size is None:
                await self._repo.fail_staging_async(job_id, owner, self._scope, "invalid_storage_reference")
                progressed = True
                continue
            try:
                data = await self._storage.get_async(key)
            except StorageMissing:
                # A late upload might still be in flight. Only terminally fail an old missing intent.
                if created_at < datetime.now(UTC) - timedelta(seconds=300):
                    await self._repo.fail_staging_async(job_id, owner, self._scope, "staging_abandoned")
                    progressed = True
                continue
            except StorageUnavailable:
                # An outage must not convert a recoverable intent into a false terminal success/failure.
                continue
            if len(data) != expected_size or hashlib.sha256(data).hexdigest() != checksum:
                await self._repo.fail_staging_async(job_id, owner, self._scope, "integrity_mismatch")
                progressed = True
            elif await self._repo.mark_queued_async(job_id, owner, self._scope):
                progressed = True
        return progressed

    async def run_once_async(self, worker_id: str) -> bool:
        claim = await self._repo.claim_async(worker_id, self._scope, self._cfg.lease_seconds)
        if claim is None:
            return await self._recover_staging_async()
        job_id, token, key, expected_hash, expected_size, version_id, mime = claim
        stop = asyncio.Event()
        heartbeat = asyncio.create_task(self._heartbeat_async(job_id, token, stop))
        ok, retriable, code = False, False, None
        chunks = None
        try:
            if not key or expected_size is None:
                code = "invalid_storage_reference"
            else:
                contents = await self._storage.get_async(key)
                if len(contents) != expected_size or hashlib.sha256(contents).hexdigest() != expected_hash:
                    code = "integrity_mismatch"
                else:
                    # The existing quarantine and malware gate always precedes parsing.
                    await self._scanner.scan_async(contents)
                    pages = await self._extractor.extract_async(contents, mime, limits=self._processing)
                    chunks = chunk_pages(
                        version_id,
                        pages,
                        max_chars=self._processing.max_chunk_chars,
                        overlap=self._processing.chunk_overlap_chars,
                    )
                    ok = True
        except MalwareDetected:
            code = "malware_detected"
        except ProcessingRejected as exc:
            code = exc.code
            retriable = code == "extraction_timeout"
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
        await self._repo.finish_async(job_id, token, ok, code, retriable, chunks=chunks)
        return True
