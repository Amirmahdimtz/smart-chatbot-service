"""Group B: actual CPU model + PostgreSQL authoritative chunk + authenticated Qdrant.

Only synthetic unpublished source data. Direct version fixture is NOT approval.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from uuid import uuid4

import pytest
from qdrant_client import models
from sqlalchemy import update

from src.core.services.indexing.index_manifest import IndexContractError
from src.core.services.persian_text.persian_processing import normalize_persian
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.models.entities import DocumentVersion, KnowledgeChunk, KnowledgeDocument, KnowledgeSource
from src.infrastructure.providers.embedding.candidate_cpu_embedding_provider import CandidateCpuEmbeddingProvider
from src.infrastructure.providers.qdrant.index_staging_service import IndexStagingService
from src.infrastructure.providers.qdrant.qdrant_provider import QdrantProvider
from src.infrastructure.repositories.indexing.postgres_index_source_repository import PostgresIndexSourceRepository
from src.infrastructure.services.indexing.synthetic_candidate_index_coordinator import SyntheticCandidateIndexCoordinator
from src.infrastructure.utils.config_reader import ConfigReader


def test_real_experimental_embedding_pg_qdrant_e2e_and_revoke(monkeypatch):
    if os.environ.get("SCB_PHASE07_REAL_TEST_ENABLED") != "true":
        pytest.skip("Genuine isolated PostgreSQL+Qdrant+model execution not configured")
    assert os.environ["SCB_ENV"] == "development"
    assert os.environ["SCB_ZONE"] == "internal"
    assert os.environ["SCB_DATABASE_URL"].endswith("/scb_phase07_test")
    assert os.environ["SCB_PHASE04_TEST_QDRANT_URL"] == "http://127.0.0.1:6333"
    candidate = os.environ["SCB_PHASE07_REAL_CANDIDATE"]
    monkeypatch.setenv("SCB_QDRANT_COLLECTION_PREFIX", "scb_p07_real_" + uuid4().hex[:8])
    container = bootstrap_di()
    cfg = container.resolve(ConfigReader)
    db = container.resolve(PsqlDbContext)
    qdrant = container.resolve(QdrantProvider)
    source_repo = container.resolve(PostgresIndexSourceRepository)
    stager = container.resolve(IndexStagingService)
    encoder = CandidateCpuEmbeddingProvider(cfg, candidate=candidate)
    service = SyntheticCandidateIndexCoordinator(source_repo, encoder, stager, cfg)
    source_id, document_id, version_id = uuid4(), uuid4(), uuid4()
    principal = "synthetic-owner-" + uuid4().hex
    texts = [
        "بخش یک: مدت بررسی سند نمونه هفت روز است.",
        "بخش دوم: مسئول پذیرش درخواست، مالک پژوهش است.",
        "بخش سوم: داده‌های منسوخ در گزارش جدید حذف می‌شوند.",
    ]
    chunk_ids = [uuid4() for _ in texts]

    async def exercise():
        await db.start_async()
        await qdrant.start_async()
        await encoder.start_async()
        try:
            # Construct only an isolated TEST read-state fixture; Phase07 real
            # ingestion/approval transitions are not represented or validated.
            async with db.transaction_async() as session:
                session.add(
                    KnowledgeSource(
                        id=source_id,
                        deployment_scope="internal",
                        owner_principal_id=principal,
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
                        title="Synthetic Persian embedding CI source",
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
                for ordinal, raw in enumerate(texts):
                    canonical = normalize_persian(raw)
                    session.add(
                        KnowledgeChunk(
                            id=chunk_ids[ordinal],
                            version_id=version_id,
                            deployment_scope="internal",
                            ordinal=ordinal,
                            checksum_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
                            canonical_text=canonical,
                            original_text=raw,
                            page_number=ordinal + 1,
                            source_start=0,
                            source_end=len(raw),
                            processor_version="fa-structure-v1",
                            normalizer_version="fa-nfc-normalizer-v1",
                        )
                    )
            with pytest.raises(IndexContractError):
                await service.stage_version_async(version_id=version_id, principal_id="foreign", domain="research")
            with pytest.raises(IndexContractError):
                await service.stage_version_async(version_id=version_id, principal_id=principal, domain="hr")
            manifest, ids = await service.stage_version_async(
                version_id=version_id, principal_id=principal, domain="research"
            )
            assert manifest.model_revision == encoder.revision
            assert manifest.model_id == encoder.model_id
            assert manifest.embedding_dimension == 384
            assert manifest.document_id == document_id
            assert manifest.chunk_ids == tuple(chunk_ids)
            assert len(ids) == 3
            assert encoder.load_count == 1
            assert (await service.stage_version_async(
                version_id=version_id, principal_id=principal, domain="research"
            ))[1] == ids
            assert encoder.load_count == 1

            points = await qdrant._client.retrieve(
                collection_name=qdrant.collection_name,
                ids=ids,
                with_payload=True,
                with_vectors=True,
            )
            assert len(points) == 3
            assert all(p.payload["published"] is False for p in points)
            assert all(p.payload["document_id"] == str(document_id) for p in points)
            assert all(len(p.vector) == 384 for p in points)
            assert all(p.payload["domain"] == "research" for p in points)
            # Qdrant will return ZERO published hits, even if a query uses an
            # actual vector from the model or knows the document ID.
            actual_query = (await encoder.embed_async(["مسئول پذیرش کیست؟"], kind="query"))[0]
            hidden = await qdrant._client.query_points(
                collection_name=qdrant.collection_name,
                query=actual_query,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key="published", match=models.MatchValue(value=True))]
                ),
                limit=10,
            )
            assert hidden.points == []
            async with db.transaction_async() as session:
                await session.execute(
                    update(DocumentVersion)
                    .where(DocumentVersion.id == version_id)
                    .values(state="revoked")
                )
            with pytest.raises(IndexContractError):
                await service.stage_version_async(version_id=version_id, principal_id=principal, domain="research")
            stored = await qdrant._client.retrieve(
                collection_name=qdrant.collection_name, ids=ids, with_payload=True
            )
            assert len(stored) == 3
            assert all(p.payload["published"] is False for p in stored)
        finally:
            await encoder.close_async()
            await qdrant.close_async()
            await db.close_async()

    asyncio.run(exercise())
