"""Actual Postgres-only durable job lease/concurrency tests on synthetic disposable DB."""

from __future__ import annotations

import asyncio
import os
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.engine import make_url

from src.core.services.ingestion.ingestion_service import IngestionService
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.models.entities import DocumentVersion, KnowledgeDocument, KnowledgeSource
from src.infrastructure.models.ingestion_job import IngestionJob


def _disposable_url() -> str:
    url = os.environ.get("SCB_PHASE03_TEST_DATABASE_URL")
    if not url:
        pytest.skip("No real isolated PostgreSQL configured")
    parsed = make_url(url)
    if parsed.drivername != "postgresql+asyncpg" or parsed.host not in {"127.0.0.1", "localhost"} or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        pytest.fail("Refusing integration against non-disposable PostgreSQL")
    return url


def test_durable_job_lease_recovery_and_idempotency(monkeypatch):
    url = _disposable_url()
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.setenv("SCB_DATABASE_ENABLED", "true")
    monkeypatch.setenv("SCB_DATABASE_URL", url)
    container = bootstrap_di()
    db = container.resolve(PsqlDbContext)
    service = container.resolve(IngestionService)

    async def exercise():
        await db.start_async()
        try:
            principal = "synthetic-" + str(uuid4())
            async with db.transaction_async() as session:
                source = KnowledgeSource(owner_principal_id=principal, deployment_scope="public", domain="research")
                session.add(source)
                await session.flush()
                doc = KnowledgeDocument(source_id=source.id, deployment_scope="public", title="synthetic document")
                session.add(doc)
                await session.flush()
                version = DocumentVersion(
                    document_id=doc.id, deployment_scope="public", version_number=1,
                    checksum_sha256="f" * 64,
                )
                session.add(version)
                await session.flush()
                source_id, version_id = source.id, version.id

            kwargs = dict(
                principal=principal, scope="public", source_id=source_id,
                version_id=version_id, idempotency_key="first", max_attempts=2,
            )
            first, duplicate = await asyncio.gather(
                service.enqueue_async(**kwargs), service.enqueue_async(**kwargs)
            )
            assert first.id == duplicate.id
            assert first.status == "queued"
            with pytest.raises(ValueError):
                await service.enqueue_async(**(kwargs | {"max_attempts": 3}))
            with pytest.raises(PermissionError):
                await service.enqueue_async(**(kwargs | {"principal": "another-owner"}))
            with pytest.raises(PermissionError):
                await service.enqueue_async(**(kwargs | {"scope": "internal"}))

            claims = await asyncio.gather(
                *(service.claim_next_async(scope="public", worker_id=f"worker-{i}", lease_seconds=30)
                  for i in range(4))
            )
            active = [claim for claim in claims if claim is not None]
            assert len(active) == 1
            assert active[0].id == first.id and active[0].attempts == 1
            original_token = active[0].lease_token
            assert await service.heartbeat_async(
                scope="public", job_id=first.id, lease_token=original_token, lease_seconds=30
            )
            assert not await service.complete_async(
                scope="public", job_id=first.id, lease_token=uuid4()
            )
            async with db.transaction_async() as session:
                now = await session.scalar(select(func.now()))
                await session.execute(
                    update(IngestionJob)
                    .where(IngestionJob.id == first.id)
                    .values(lease_expires_at=now - timedelta(seconds=1))
                )
            recovered = await service.claim_next_async(scope="public", worker_id="worker-recover", lease_seconds=30)
            assert recovered and recovered.id == first.id and recovered.attempts == 2
            assert recovered.lease_token != original_token
            assert not await service.complete_async(
                scope="public", job_id=first.id, lease_token=original_token
            )
            assert not await service.fail_async(
                scope="public", job_id=first.id, lease_token=original_token, error_code="TEST_FAILURE"
            )
            assert await service.fail_async(
                scope="public", job_id=first.id, lease_token=recovered.lease_token, error_code="TEST_FAILURE"
            )
            async with db.transaction_async() as session:
                stored = await session.get(IngestionJob, first.id)
                assert stored.status == "dead_letter" and stored.attempts == 2
                assert stored.error_code == "TEST_FAILURE"
            assert await service.claim_next_async(scope="public", worker_id="worker-other") is None

            followup = await service.enqueue_async(**(kwargs | {"idempotency_key": "second"}))
            claim2 = await service.claim_next_async(scope="public", worker_id="worker-done")
            assert claim2 and claim2.id == followup.id
            assert await service.complete_async(
                scope="public", job_id=claim2.id, lease_token=claim2.lease_token
            )
            assert not await service.complete_async(
                scope="public", job_id=claim2.id, lease_token=claim2.lease_token
            )
            async with db.transaction_async() as session:
                assert (await session.get(IngestionJob, claim2.id)).status == "completed"

            stuck = await service.enqueue_async(**(kwargs | {"idempotency_key": "third", "max_attempts": 1}))
            expired = await service.claim_next_async(scope="public", worker_id="worker-crash")
            assert expired and expired.id == stuck.id
            async with db.transaction_async() as session:
                now = await session.scalar(select(func.now()))
                await session.execute(
                    update(IngestionJob)
                    .where(IngestionJob.id == stuck.id)
                    .values(lease_expires_at=now - timedelta(seconds=1))
                )
            assert await service.claim_next_async(scope="public", worker_id="worker-sweep") is None
            async with db.transaction_async() as session:
                retired = await session.get(IngestionJob, stuck.id)
                assert retired.status == "dead_letter" and retired.error_code == "LEASE_EXHAUSTED"
        finally:
            await db.close_async()

    asyncio.run(exercise())
