"""Group B: genuine disposable PostgreSQL lease, terminal error and audit tests."""

from __future__ import annotations

import asyncio
import hashlib
import os
from uuid import uuid4

import pytest
from sqlalchemy import select

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.models.entities import KnowledgeChunk
from src.infrastructure.models.ingestion import IngestionAuditEvent
from src.infrastructure.repositories.ingestion.ingestion_repository import IngestionRepository


@pytest.mark.parametrize(
    ("chunk_count", "expected_error"),
    [(0, "empty_chunk_batch"), (4097, "too_many_chunks")],
)
def test_real_postgres_rejects_invalid_chunk_batch_as_terminal_audited_failure(chunk_count, expected_error):
    if os.environ.get("SCB_PHASE05_TEST_ENABLED") != "true":
        pytest.skip("Real isolated PostgreSQL CI environment is not configured")
    assert os.environ["SCB_ENV"] == "development"
    assert os.environ["SCB_ZONE"] == "internal"
    assert os.environ["SCB_DATABASE_URL"].endswith("/scb_phase05_test")
    container = bootstrap_di()
    db = container.resolve(PsqlDbContext)
    repo = container.resolve(IngestionRepository)

    async def exercise():
        await db.start_async()
        try:
            actor = "synthetic-chunk-bound-" + uuid4().hex
            source = await repo.create_source_async(actor, "internal", "research")
            contents = ("synthetic-fixture-" + uuid4().hex).encode()
            checksum = hashlib.sha256(contents).hexdigest()
            job, version, created = await repo.stage_async(
                source.id,
                actor,
                "internal",
                "fixture.txt",
                "text/plain",
                len(contents),
                checksum,
                uuid4().hex,
                2,
            )
            assert created
            assert await repo.mark_queued_async(job.id, actor, "internal")
            claimed = await repo.claim_async("bnd", "internal", 45)
            assert claimed is not None and claimed[0] == job.id
            # Invalid batches are rejected before materializing any chunk row.
            bad_chunks = [object()] * chunk_count
            assert await repo.finish_async(job.id, claimed[1], True, chunks=bad_chunks)
            stored = await repo.get_job_owned_async(job.id, actor, "internal")
            assert stored is not None
            assert stored[0].status == "dead"
            assert stored[0].error_code == expected_error
            assert stored[1].state == "failed"
            assert not await repo.finish_async(job.id, claimed[1], True, chunks=bad_chunks)
            async with db.transaction_async() as session:
                chunks = (
                    await session.scalars(select(KnowledgeChunk).where(KnowledgeChunk.version_id == version.id))
                ).all()
                audits = (
                    await session.scalars(select(IngestionAuditEvent).where(IngestionAuditEvent.job_id == job.id))
                ).all()
                assert chunks == []
                assert any(event.event == "dead" and event.code == expected_error for event in audits)
        finally:
            await db.close_async()

    asyncio.run(exercise())
