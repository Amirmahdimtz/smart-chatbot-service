"""Phase08 Group B real isolated PostgreSQL authorization/revocation test.

The synthetic test directly changes database state to probe the READ gate.
This does not implement or verify Phase07 approval/publication transitions.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from uuid import uuid4

import pytest
from sqlalchemy import update

from src.core.services.retrieval.retrieval_contract import FusedCandidate
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.models.entities import DocumentVersion, KnowledgeChunk, KnowledgeDocument, KnowledgeSource
from src.infrastructure.repositories.retrieval.retrieval_evidence_repository import RetrievalEvidenceRepository


def test_real_postgres_authorization_deny_prepublication_and_revoke():
    if os.environ.get("SCB_PHASE05_TEST_ENABLED") != "true":
        pytest.skip("Isolated Phase05 PostgreSQL ingestion test environment absent")
    assert os.environ["SCB_ENV"] == "development"
    assert os.environ["SCB_ZONE"] == "internal"
    assert os.environ["SCB_DATABASE_URL"].endswith("/scb_phase05_test")
    container = bootstrap_di()
    db = container.resolve(PsqlDbContext)
    repo = container.resolve(RetrievalEvidenceRepository)
    actor = "phase08-synthetic-" + uuid4().hex
    other = "phase08-other-" + uuid4().hex
    source_id, doc_id, version_id, chunk_id = (uuid4() for _ in range(4))
    text = "ماده ۱۲ قانون آزمایشی"
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
    candidate = FusedCandidate(
        chunk_id=chunk_id,
        document_id=doc_id,
        version_id=version_id,
        rrf_score=1 / 61,
        channels=("dense",),
    )

    async def exercise():
        await db.start_async()
        try:
            async with db.transaction_async() as session:
                session.add(
                    KnowledgeSource(
                        id=source_id,
                        deployment_scope="internal",
                        owner_principal_id=actor,
                        domain="research",
                        source_type="file",
                        status="active",
                        classification="synthetic_unclassified",
                        policy_ref="synthetic-only",
                    )
                )
                session.add(
                    KnowledgeDocument(
                        id=doc_id,
                        source_id=source_id,
                        deployment_scope="internal",
                        title="Synthetic policy fixture",
                    )
                )
                session.add(
                    DocumentVersion(
                        id=version_id,
                        document_id=doc_id,
                        deployment_scope="internal",
                        version_number=1,
                        checksum_sha256=checksum,
                        state="awaiting_approval",
                    )
                )
                session.add(
                    KnowledgeChunk(
                        id=chunk_id,
                        version_id=version_id,
                        deployment_scope="internal",
                        ordinal=0,
                        checksum_sha256=checksum,
                        original_text=text,
                        canonical_text=text,
                        page_number=1,
                        source_start=10,
                        source_end=10 + len(text),
                    )
                )

            async def fetch(actor_name=actor, domain="research", candidates=None):
                return await repo.reauthorize_async(
                    candidates=candidates if candidates is not None else [candidate],
                    principal_id=actor_name,
                    domain=domain,
                    scope="internal",
                )

            # Even forged Qdrant "published" payloads cannot override PG's
            # authoritative awaiting_approval state.
            assert await fetch() == []
            async with db.transaction_async() as session:
                await session.execute(
                    update(DocumentVersion)
                    .where(DocumentVersion.id == version_id)
                    .values(state="published")
                )
            # Manual fixture state is NOT evidence of Phase07 approval.
            assert await fetch(actor_name=other) == []
            assert await fetch(domain="religion") == []
            assert await fetch(candidates=[FusedCandidate(chunk_id, uuid4(), version_id, 0.01, ("dense",))]) == []
            accepted = await fetch()
            assert len(accepted) == 1
            assert accepted[0].canonical == text
            assert accepted[0].source_start == 10
            assert accepted[0].source_end == 10 + len(text)

            async with db.transaction_async() as session:
                await session.execute(
                    update(DocumentVersion)
                    .where(DocumentVersion.id == version_id)
                    .values(state="revoked")
                )
            assert await fetch() == []
            async with db.transaction_async() as session:
                await session.execute(
                    update(DocumentVersion)
                    .where(DocumentVersion.id == version_id)
                    .values(state="published")
                )
                await session.execute(
                    update(KnowledgeSource)
                    .where(KnowledgeSource.id == source_id)
                    .values(status="disabled")
                )
            assert await fetch() == []
        finally:
            await db.close_async()

    asyncio.run(exercise())
