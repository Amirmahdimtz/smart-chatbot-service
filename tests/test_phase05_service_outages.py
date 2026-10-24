"""Real isolated service outage/recovery tests against disposable CI containers only."""

from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.core.services.ingestion.ingestion_worker_service import IngestionWorkerService
from src.infrastructure.context.sql_db.psql_dbcontext import DatabaseUnavailable, PsqlDbContext
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.models.ingestion import IngestionJob
from src.infrastructure.providers.scanner.clamav_scanner import ClamAvScanner, MalwareDetected, ScanUnavailable
from src.infrastructure.providers.storage.quarantine_storage import QuarantineStorage, StorageUnavailable
from src.infrastructure.repositories.ingestion.ingestion_repository import IngestionRepository


def _guard() -> None:
    if os.getenv("SCB_PHASE05_TEST_ENABLED") != "true":
        pytest.skip("Only disposable real Phase05 integration services can run these tests")
    assert os.getenv("CI") == "true", "Fault injection must run on an isolated CI runner"
    assert os.getenv("SCB_ENV") == "development"
    assert os.getenv("SCB_ZONE") == "internal"
    assert os.getenv("SCB_DATABASE_URL", "").endswith("/scb_phase05_test")
    assert os.getenv("SCB_INGESTION_S3_URL") == "http://127.0.0.1:9000"
    assert shutil.which("docker"), "Docker CLI is mandatory for actual outage testing"


def _docker(*parts: str) -> str:
    command = subprocess.run(["docker", *parts], check=True, capture_output=True, text=True, timeout=20)
    return command.stdout.strip()


def _postgres_container() -> str:
    matches = []
    for line in _docker("ps", "--format", "{{.ID}} {{.Image}}").splitlines():
        ident, image = line.split(maxsplit=1)
        if image == "postgres:16":
            matches.append(ident)
    assert len(matches) == 1, "Only the uniquely identified disposable CI PostgreSQL may be paused"
    return matches[0]


async def _stage(repo: IngestionRepository, data: bytes):
    owner = "synthetic-" + uuid4().hex
    source = await repo.create_source_async(owner, "internal", "research")
    checksum = hashlib.sha256(data).hexdigest()
    job, version, created = await repo.stage_async(
        source.id,
        owner,
        "internal",
        "outage.txt",
        "text/plain",
        len(data),
        checksum,
        uuid4().hex,
        3,
    )
    assert created
    return owner, job, version, checksum


def test_real_s3_pause_unpause_preserves_quarantine_and_job():
    _guard()

    async def exercise():
        container = bootstrap_di()
        db = container.resolve(PsqlDbContext)
        repo = container.resolve(IngestionRepository)
        store = container.resolve(QuarantineStorage)
        worker = container.resolve(IngestionWorkerService)
        await db.start_async()
        try:
            await store.start_async()
            try:
                payload = ("s3-pause-" + uuid4().hex).encode()
                owner, job, version, checksum = await _stage(repo, payload)
                await store.put_async(version.object_key, payload, checksum)
                assert await repo.mark_queued_async(job.id, owner, "internal")
                _docker("pause", "scb-phase05-s3")
                try:
                    with pytest.raises(StorageUnavailable):
                        await store.get_async(version.object_key)
                    # Never accept a scan while quarantine storage is frozen.
                    assert (await repo.get_job_owned_async(job.id, owner, "internal"))[0].status == "queued"
                finally:
                    _docker("unpause", "scb-phase05-s3")
                assert await store.get_async(version.object_key) == payload
                assert await worker.run_once_async("s3-restored")
                accepted = await repo.get_job_owned_async(job.id, owner, "internal")
                assert accepted[0].status == "completed"
                assert accepted[1].state == "awaiting_approval"
            finally:
                await store.close_async()
        finally:
            await db.close_async()

    asyncio.run(exercise())


def test_real_clamav_pause_unpause_requires_rescan():
    _guard()

    async def exercise():
        container = bootstrap_di()
        db = container.resolve(PsqlDbContext)
        repo = container.resolve(IngestionRepository)
        store = container.resolve(QuarantineStorage)
        worker = container.resolve(IngestionWorkerService)
        await db.start_async()
        try:
            await store.start_async()
            try:
                payload = ("clamav-pause-" + uuid4().hex).encode()
                owner, job, version, checksum = await _stage(repo, payload)
                await store.put_async(version.object_key, payload, checksum)
                assert await repo.mark_queued_async(job.id, owner, "internal")
                _docker("pause", "scb-phase05-clamav")
                try:
                    assert await worker.run_once_async("clamav-paused")
                    waiting = await repo.get_job_owned_async(job.id, owner, "internal")
                    assert waiting[0].status == "retry_wait"
                    assert waiting[0].error_code == "dependency_unavailable"
                    assert waiting[1].state != "awaiting_approval"
                finally:
                    _docker("unpause", "scb-phase05-clamav")
                async with db.transaction_async() as session:
                    row = await session.get(IngestionJob, job.id)
                    row.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)
                assert await worker.run_once_async("clamav-restored")
                accepted = await repo.get_job_owned_async(job.id, owner, "internal")
                assert accepted[0].status == "completed"
                assert accepted[1].state == "awaiting_approval"
            finally:
                await store.close_async()
        finally:
            await db.close_async()

    asyncio.run(exercise())


def test_real_postgresql_pause_denies_start_then_recovers():
    _guard()

    async def exercise():
        db = bootstrap_di().resolve(PsqlDbContext)
        await db.start_async()
        await db.close_async()
        postgres_id = _postgres_container()
        _docker("pause", postgres_id)
        try:
            with pytest.raises(DatabaseUnavailable):
                await db.start_async()
        finally:
            _docker("unpause", postgres_id)
        # A previously failed startup must not poison the next lifespan.
        await db.start_async()
        try:
            repo = bootstrap_di().resolve(IngestionRepository)
            # Fresh provider receives its own DB; verify recovered state through
            # the database-bound provider rather than a mock or stale pool.
            independent_db = repo._db
            await independent_db.start_async()
            try:
                owner = "synthetic-" + uuid4().hex
                source = await repo.create_source_async(owner, "internal", "research")
                assert (await repo.get_source_owned_async(source.id, owner, "internal")).id == source.id
            finally:
                await independent_db.close_async()
        finally:
            await db.close_async()

    asyncio.run(exercise())


async def _wait_restored(operation, retry_exceptions, *, attempts: int = 90):
    """A cold-started service must become actually usable, not just report a PID."""
    for _ in range(attempts):
        try:
            return await operation()
        except retry_exceptions:
            await asyncio.sleep(1)
    pytest.fail("Dependency did not recover after a real Docker process restart")


def test_s3_cold_restart_preserves_immutable_quarantined_bytes():
    _guard()

    async def exercise():
        container = bootstrap_di()
        db = container.resolve(PsqlDbContext)
        repo = container.resolve(IngestionRepository)
        store = container.resolve(QuarantineStorage)
        worker = container.resolve(IngestionWorkerService)
        await db.start_async()
        try:
            await store.start_async()
            try:
                payload = ("s3-restart-" + uuid4().hex).encode()
                owner, job, version, checksum = await _stage(repo, payload)
                await store.put_async(version.object_key, payload, checksum)
                assert await repo.mark_queued_async(job.id, owner, "internal")
                # Docker restart forcibly stops and cold-starts the actual S3
                # server process; the service's persisted /data is retained.
                _docker("restart", "--time", "1", "scb-phase05-s3")
                restored = await _wait_restored(
                    lambda: store.get_async(version.object_key), (StorageUnavailable,)
                )
                assert restored == payload
                assert (await repo.get_job_owned_async(job.id, owner, "internal"))[0].status == "queued"
                assert await worker.run_once_async("s3-cold-restart")
                result = await repo.get_job_owned_async(job.id, owner, "internal")
                assert result[0].status == "completed"
                assert result[1].state == "awaiting_approval"
            finally:
                await store.close_async()
        finally:
            await db.close_async()

    asyncio.run(exercise())


def test_clamav_cold_restart_restores_genuine_malware_verdict():
    _guard()
    eicar = b"X5O!P%@AP[4\\\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

    async def exercise():
        container = bootstrap_di()
        db = container.resolve(PsqlDbContext)
        repo = container.resolve(IngestionRepository)
        store = container.resolve(QuarantineStorage)
        scanner = container.resolve(ClamAvScanner)
        worker = container.resolve(IngestionWorkerService)
        await db.start_async()
        try:
            await store.start_async()
            try:
                payload = ("clamav-restart-" + uuid4().hex).encode()
                owner, job, version, checksum = await _stage(repo, payload)
                await store.put_async(version.object_key, payload, checksum)
                assert await repo.mark_queued_async(job.id, owner, "internal")
                _docker("restart", "--time", "1", "scb-phase05-clamav")
                await _wait_restored(lambda: scanner.scan_async(payload), (ScanUnavailable,))
                with pytest.raises(MalwareDetected):
                    await scanner.scan_async(eicar)
                # No acceptance before an actual post-restart clean verdict.
                assert (await repo.get_job_owned_async(job.id, owner, "internal"))[0].status == "queued"
                assert await worker.run_once_async("clamav-cold-restart")
                result = await repo.get_job_owned_async(job.id, owner, "internal")
                assert result[0].status == "completed"
                assert result[1].state == "awaiting_approval"
            finally:
                await store.close_async()
        finally:
            await db.close_async()

    asyncio.run(exercise())


def test_postgresql_cold_restart_reclaims_persisted_inflight_lease():
    _guard()

    async def exercise():
        container = bootstrap_di()
        db = container.resolve(PsqlDbContext)
        repo = container.resolve(IngestionRepository)
        store = container.resolve(QuarantineStorage)
        worker = container.resolve(IngestionWorkerService)
        await db.start_async()
        try:
            await store.start_async()
            try:
                payload = ("pg-restart-" + uuid4().hex).encode()
                owner, job, version, checksum = await _stage(repo, payload)
                await store.put_async(version.object_key, payload, checksum)
                assert await repo.mark_queued_async(job.id, owner, "internal")
                old_lease = await repo.claim_async("before-postgres-restart", "internal", 2)
                assert old_lease and old_lease[0] == job.id
                await db.close_async()
                # GitHub Actions owns this container: cold-restart its real
                # server process without deleting the disposable DB volume.
                _docker("restart", "--time", "1", _postgres_container())
                await _wait_restored(db.start_async, (DatabaseUnavailable,))
                await asyncio.sleep(2.2)
                # A pre-crash owner must never be able to acknowledge the job.
                assert not await repo.finish_async(job.id, old_lease[1], True)
                assert await worker.run_once_async("postgres-cold-restart")
                result = await repo.get_job_owned_async(job.id, owner, "internal")
                assert result[0].status == "completed"
                assert result[1].state == "awaiting_approval"
            finally:
                await store.close_async()
        finally:
            await db.close_async()

    asyncio.run(exercise())
