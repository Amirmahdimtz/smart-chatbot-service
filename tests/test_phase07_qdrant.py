"""Phase07 Group B: actual isolated Qdrant pre-publication upsert/readback.

Vectors are explicitly synthetic fixtures, NOT output of an approved embedding
model. Passing this test cannot satisfy D-03, model quality or publish DoD.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from uuid import uuid4

import pytest
from qdrant_client import models

from src.core.services.indexing.index_manifest import (
    IndexSourceChunk,
    build_index_manifest,
    validate_embedding_vectors,
)
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.providers.qdrant.index_staging_service import IndexStagingService
from src.infrastructure.providers.qdrant.qdrant_provider import QdrantProvider
from src.infrastructure.utils.config_reader import ConfigReader


def test_real_qdrant_hidden_staging_replay_and_scope(monkeypatch):
    url = os.environ.get("SCB_PHASE04_TEST_QDRANT_URL")
    if not url:
        pytest.skip("Real isolated authenticated Qdrant not available")
    assert url == "http://127.0.0.1:6333"
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "internal")
    monkeypatch.setenv("SCB_QDRANT_ENABLED", "true")
    monkeypatch.setenv("SCB_QDRANT_ZONE", "internal")
    monkeypatch.setenv("SCB_QDRANT_URL", url)
    monkeypatch.setenv("SCB_QDRANT_API_KEY", os.environ["SCB_PHASE04_TEST_QDRANT_KEY"])
    monkeypatch.setenv("SCB_QDRANT_DIMENSION", "4")
    monkeypatch.setenv("SCB_QDRANT_COLLECTION_PREFIX", "scb_p07_" + uuid4().hex[:12])
    container = bootstrap_di()
    config = container.resolve(ConfigReader)
    provider = container.resolve(QdrantProvider)
    stager = container.resolve(IndexStagingService)
    version_id = uuid4()
    document_id = uuid4()
    chunks = []
    for ordinal in range(7):
        raw = f"ماده {ordinal}: متن آزمایشی فارسی"
        chunks.append(
            IndexSourceChunk(
                id=uuid4(),
                ordinal=ordinal,
                canonical_text=raw,
                checksum_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                processor_version="fa-structure-v1",
                normalizer_version="fa-nfc-normalizer-v1",
                page_number=ordinal // 3 + 1,
                source_start=0,
                source_end=len(raw),
            )
        )
    manifest = build_index_manifest(
        document_id=document_id,
        version_id=version_id,
        scope="internal",
        domain="research",
        classification="synthetic_unclassified",
        model_id="ci_synthetic_fixture_not_model",
        model_revision="none",
        dimension=4,
        distance="Cosine",
        schema_version=config.settings.qdrant.schema_version,
        chunks=chunks,
    )
    vectors = validate_embedding_vectors(manifest, [[1, 0, 0, 0]] * len(chunks))

    async def exercise():
        await provider.start_async()
        try:
            first = await stager.stage_async(manifest, vectors)
            second = await stager.stage_async(manifest, vectors)
            assert len(first) == len(chunks) and first == second
            stored = await provider._client.retrieve(
                collection_name=provider.collection_name,
                ids=first,
                with_payload=True,
                with_vectors=False,
            )
            assert {str(item.id) for item in stored} == set(first)
            assert all(point.payload["published"] is False for point in stored)
            assert all(point.payload["deployment_scope"] == "internal" for point in stored)
            hidden = await provider._client.query_points(
                collection_name=provider.collection_name,
                query=[1.0, 0, 0, 0],
                query_filter=models.Filter(
                    must=[models.FieldCondition(key="published", match=models.MatchValue(value=True))]
                ),
                limit=10,
            )
            assert hidden.points == []
        finally:
            await provider.close_async()

    asyncio.run(exercise())
