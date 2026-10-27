"""Phase08 Group B real Qdrant filtered candidate lookup, no publication claim.

Uses synthetic known vectors and a deny-all authority stub; real PostgreSQL
revocation behavior is exercised separately in test_phase08_postgres.py.
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.core.services.retrieval.retrieval_query_service import RetrievalQueryService
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.providers.qdrant.qdrant_provider import QdrantProvider, VectorRecord
from src.infrastructure.utils.config_reader import ConfigReader


def test_real_qdrant_filtered_candidates_cannot_bypass_deny_all_authority(monkeypatch):
    url = os.environ.get("SCB_PHASE04_TEST_QDRANT_URL")
    if not url:
        pytest.skip("Isolated authenticated Qdrant unavailable")
    assert url == "http://127.0.0.1:6333"
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "internal")
    monkeypatch.setenv("SCB_QDRANT_ENABLED", "true")
    monkeypatch.setenv("SCB_QDRANT_ZONE", "internal")
    monkeypatch.setenv("SCB_QDRANT_URL", url)
    monkeypatch.setenv("SCB_QDRANT_API_KEY", os.environ["SCB_PHASE04_TEST_QDRANT_KEY"])
    monkeypatch.setenv("SCB_QDRANT_DIMENSION", "4")
    monkeypatch.setenv("SCB_QDRANT_COLLECTION_PREFIX", "scb_p08_" + uuid4().hex[:12])
    container = bootstrap_di()
    cfg = container.resolve(ConfigReader)
    qdrant = container.resolve(QdrantProvider)
    owned_id, other_id = uuid4(), uuid4()

    class DenyAllAuthority:
        def __init__(self):
            self.calls = []

        async def reauthorize_async(self, **kwargs):
            self.calls.append(kwargs)
            return []

    deny = DenyAllAuthority()
    enabled = cfg.settings.model_copy(update={"database": cfg.settings.database.model_copy(update={"enabled": True})})
    service = RetrievalQueryService(qdrant, deny, SimpleNamespace(settings=enabled))

    async def exercise():
        await qdrant.start_async()
        try:
            await qdrant.ensure_collection_async()
            await qdrant.activate_collection_async()
            good = VectorRecord(
                chunk_id=uuid4(),
                document_id=owned_id,
                document_version_id=uuid4(),
                domain="research",
                classification="synthetic_unclassified",
                vector=[1.0, 0.0, 0.0, 0.0],
                published=True,  # TEST-ONLY injection, not a Phase07 approval operation
            )
            other = VectorRecord(
                chunk_id=uuid4(),
                document_id=other_id,
                document_version_id=uuid4(),
                domain="research",
                classification="synthetic_unclassified",
                vector=[1.0, 0.0, 0.0, 0.0],
                published=True,
            )
            wrong_domain = VectorRecord(
                chunk_id=uuid4(),
                document_id=owned_id,
                document_version_id=uuid4(),
                domain="religion",
                classification="synthetic_unclassified",
                vector=[1.0, 0.0, 0.0, 0.0],
                published=True,
            )
            await qdrant.upsert_async([good, other, wrong_domain])
            assert (
                await service.retrieve_synthetic_dense_async(
                    query="پرسش ١٢",
                    vector=[1.0, 0.0, 0.0, 0.0],
                    principal_id="synthetic-owner",
                    domain="research",
                    allowed_document_ids=[owned_id],
                )
                == []
            )
            assert len(deny.calls) == 1
            authorized_candidates = deny.calls[0]["candidates"]
            assert [x.chunk_id for x in authorized_candidates] == [good.chunk_id]
            assert deny.calls[0]["scope"] == "internal"
        finally:
            await qdrant.close_async()

    asyncio.run(exercise())
