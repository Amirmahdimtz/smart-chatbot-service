"""Phase07 Group B: actual PG fenced job, genuine model, Qdrant publish/revoke.

Synthetic Development-only. The reviewer is a test fixture, NOT an IdP actor.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from uuid import uuid4

import pytest
from qdrant_client import models
from sqlalchemy import select

from src.core.services.indexing.index_manifest import IndexContractError
from src.core.services.persian_text.persian_processing import normalize_persian
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.models.entities import DocumentVersion, KnowledgeChunk, KnowledgeDocument, KnowledgeSource
from src.infrastructure.models.indexing import IndexJob, IndexManifestRecord, IndexPublication
from src.infrastructure.providers.embedding.candidate_cpu_embedding_provider import CandidateCpuEmbeddingProvider
from src.infrastructure.providers.qdrant.index_staging_service import IndexStagingService
from src.infrastructure.providers.qdrant.qdrant_provider import QdrantProvider
from src.infrastructure.repositories.indexing.index_job_repository import IndexJobRepository
from src.infrastructure.repositories.indexing.postgres_index_source_repository import PostgresIndexSourceRepository
from src.infrastructure.services.indexing.durable_index_lifecycle_service import DurableIndexLifecycleService
from src.infrastructure.utils.config_reader import ConfigReader


def test_real_pg_fenced_index_job_publish_revoke_and_outage_cleanup(monkeypatch):
    if os.getenv("SCB_PHASE07_REAL_TEST_ENABLED") != "true":
        pytest.skip("isolated actual PostgreSQL + Qdrant + model required")
    assert os.environ["SCB_ENV"] == "development"
    assert os.environ["SCB_ZONE"] == "internal"
    assert os.environ["SCB_DATABASE_URL"].endswith("/scb_phase07_test")
    monkeypatch.setenv("SCB_QDRANT_COLLECTION_PREFIX", "scb_p07_life_" + uuid4().hex[:8])
    container = bootstrap_di()
    cfg = container.resolve(ConfigReader)
    db = container.resolve(PsqlDbContext)
    qdrant = container.resolve(QdrantProvider)
    staging = container.resolve(IndexStagingService)
    source_repo = container.resolve(PostgresIndexSourceRepository)
    jobs = container.resolve(IndexJobRepository)
    encoder = CandidateCpuEmbeddingProvider(cfg, candidate=os.environ["SCB_PHASE07_REAL_CANDIDATE"])
    lifecycle = DurableIndexLifecycleService(source_repo, jobs, encoder, staging, qdrant)
    source_id, document_id, version_id = uuid4(), uuid4(), uuid4()
    owner = "synthetic-owner-" + uuid4().hex
    texts = ["بند نخست: پرونده آموزشی فقط پس از تأیید منتشر می‌شود.", "بند دوم: نسخه منسوخ نباید در پاسخ نمایان شود."]

    async def exercise():
        await db.start_async()
        await qdrant.start_async()
        await encoder.start_async()
        try:
            async with db.transaction_async() as session:
                session.add(
                    KnowledgeSource(
                        id=source_id,
                        deployment_scope="internal",
                        owner_principal_id=owner,
                        domain="research",
                        source_type="file",
                        status="active",
                        classification="synthetic_unclassified",
                        policy_ref="synthetic-only",
                    )
                )
                await session.flush()
                session.add(
                    KnowledgeDocument(
                        id=document_id,
                        source_id=source_id,
                        deployment_scope="internal",
                        title="Synthetic controlled document",
                    )
                )
                await session.flush()
                session.add(
                    DocumentVersion(
                        id=version_id,
                        document_id=document_id,
                        deployment_scope="internal",
                        version_number=1,
                        checksum_sha256=hashlib.sha256("".join(texts).encode()).hexdigest(),
                        state="awaiting_approval",
                    )
                )
                await session.flush()
                for i, text in enumerate(texts):
                    canonical = normalize_persian(text)
                    session.add(
                        KnowledgeChunk(
                            id=uuid4(),
                            version_id=version_id,
                            deployment_scope="internal",
                            ordinal=i,
                            checksum_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
                            canonical_text=canonical,
                            original_text=text,
                            page_number=i + 1,
                            source_start=0,
                            source_end=len(text),
                            processor_version="fa-structure-v1",
                            normalizer_version="fa-nfc-normalizer-v1",
                        )
                    )
            with pytest.raises(IndexContractError):
                await lifecycle.enqueue_async(version_id=version_id, principal_id="other", domain="research")
            job_id, manifest = await lifecycle.enqueue_async(
                version_id=version_id, principal_id=owner, domain="research"
            )
            assert (await lifecycle.enqueue_async(
                version_id=version_id, principal_id=owner, domain="research"
            ))[0] == job_id
            assert await jobs.claim_async(job_id, principal_id="other") is None
            wrong_token = uuid4()
            assert not await jobs.finish_async(
                job_id, lease_token=wrong_token, manifest=manifest, point_ids=["bad"] * manifest.chunk_count
            )
            assert await lifecycle.stage_claimed_async(
                job_id=job_id, manifest=manifest, principal_id=owner
            )
            assert encoder.load_count == 1
            async with db.transaction_async() as session:
                stored_job = await session.get(IndexJob, job_id)
                receipt = await session.scalar(select(IndexManifestRecord).where(IndexManifestRecord.job_id == job_id))
                assert stored_job.status == "staged"
                assert stored_job.lease_token is None
                assert stored_job.attempts == 1
                assert receipt.manifest_json["model_revision"] == manifest.model_revision
                assert len(receipt.point_ids) == 2
                assert receipt.manifest_sha256 == manifest.canonical_checksum_sha256
            assert not await lifecycle.approve_synthetic_async(
                job_id=job_id, approver_id=owner, approval_ref="synthetic-ci", digest=manifest.canonical_checksum_sha256
            )
            assert not await lifecycle.approve_synthetic_async(
                job_id=job_id, approver_id="synthetic-reviewer", approval_ref="synthetic-ci", digest="0" * 64
            )
            assert not await lifecycle.publish_synthetic_async(job_id=job_id)
            assert await lifecycle.approve_synthetic_async(
                job_id=job_id,
                approver_id="synthetic-reviewer",
                approval_ref="synthetic-ci-manual-fixture",
                digest=manifest.canonical_checksum_sha256,
            )
            assert await lifecycle.publish_synthetic_async(job_id=job_id)
            assert await jobs.current_version_async(document_id) == version_id
            async with db.transaction_async() as session:
                assert (await session.get(DocumentVersion, version_id)).state == "published"
                assert (await session.get(IndexPublication, document_id)).active_version_id == version_id
            actual_q = (await encoder.embed_async(["چه زمانی انتشار مجاز است؟"], kind="query"))[0]
            hits = await qdrant._client.query_points(
                collection_name=qdrant.alias_name,
                query=actual_q,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key="published", match=models.MatchValue(value=True))]
                ),
                limit=10,
            )
            assert len(hits.points) == 2
            # Simulate Qdrant outage AFTER authoritative PG-first revocation.
            await qdrant.close_async()
            outcome = await lifecycle.revoke_first_async(
                version_id=version_id, owner_id=owner, domain="research"
            )
            assert outcome.pg_revoked and outcome.qdrant_cleanup_pending
            assert await jobs.current_version_async(document_id) is None
            async with db.transaction_async() as session:
                assert (await session.get(DocumentVersion, version_id)).state == "revoked"
                assert (await session.get(IndexJob, job_id)).cleanup_pending is True
            await qdrant.start_async()
            assert await lifecycle.cleanup_revoked_async(version_id=version_id)
            assert await jobs.cleanup_receipt_async(version_id) is None
            after = await qdrant._client.query_points(
                collection_name=qdrant.alias_name,
                query=actual_q,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key="published", match=models.MatchValue(value=True))]
                ),
                limit=10,
            )
            assert after.points == []
            assert not await lifecycle.publish_synthetic_async(job_id=job_id)
            repeated = await lifecycle.revoke_first_async(
                version_id=version_id, owner_id=owner, domain="research"
            )
            assert repeated.pg_revoked is False
        finally:
            await encoder.close_async()
            await qdrant.close_async()
            await db.close_async()

    asyncio.run(exercise())
