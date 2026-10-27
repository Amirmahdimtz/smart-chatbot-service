"""Phase08 Group A: deterministic fusion and fail-closed synthetic candidate authorization."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.core.services.retrieval.retrieval_contract import (
    CandidateHit,
    RetrievalContractError,
    fuse_rrf,
    normalize_query,
)
from src.core.services.retrieval.retrieval_query_service import RetrievalQueryService


def _candidate(chunk_id=None, document_id=None, version_id=None, score=0.7):
    return CandidateHit(
        chunk_id=chunk_id or uuid4(),
        document_id=document_id or uuid4(),
        version_id=version_id or uuid4(),
        score=score,
    )


def test_query_path_reuses_phase06_normalizer_and_rejects_invalid():
    assert normalize_query("  علي كاظمي ١٢ ") == "علی کاظمی 12"
    assert normalize_query("هدى؟") == "هدى؟"
    for invalid in ("  ", "\u0000 secret", "x" * 2049, ""):
        with pytest.raises(RetrievalContractError):
            normalize_query(invalid)


def test_rrf_stable_rank_dedup_and_cross_channel_evidence():
    a, b, c = _candidate(), _candidate(), _candidate()
    one = fuse_rrf([a, b], [b, c, a], rank_constant=60, limit=3)
    two = fuse_rrf([a, b], [b, c, a], rank_constant=60, limit=3)
    assert one == two
    assert [x.chunk_id for x in one] == [b.chunk_id, a.chunk_id, c.chunk_id]
    assert one[0].channels == ("dense", "lexical")
    assert len({x.chunk_id for x in one}) == 3


def test_rrf_rejects_poisoned_candidates_and_invalid_config():
    a = _candidate()
    for dense, lexical in (
        ([a, a], []),
        ([a], [replace(a, version_id=uuid4())]),
        ([_candidate(score=float("nan"))], []),
        ([_candidate(score=float("inf"))], []),
    ):
        with pytest.raises(RetrievalContractError):
            fuse_rrf(dense, lexical, rank_constant=60, limit=5)
    with pytest.raises(RetrievalContractError):
        fuse_rrf([a], [], rank_constant=0, limit=5)
    with pytest.raises(RetrievalContractError):
        fuse_rrf([a], [], rank_constant=60, limit=0)


def _settings():
    return SimpleNamespace(
        environment="development",
        deployment_zone="internal",
        ingestion=SimpleNamespace(synthetic_only=True),
        database=SimpleNamespace(enabled=True),
        qdrant=SimpleNamespace(enabled=True),
    )


def test_dense_query_never_returns_unverified_qdrant_payload():
    doc_id, version_id, chunk_id = uuid4(), uuid4(), uuid4()

    class FakeProvider:
        def __init__(self):
            self.points = []
            self.calls = []

        async def search_async(self, vector, **kwargs):
            self.calls.append(kwargs)
            return self.points

    class FakeAuthoritativeRepository:
        def __init__(self):
            self.decisions = []
            self.granted = []

        async def reauthorize_async(self, **kwargs):
            self.decisions.append(kwargs)
            return self.granted

    qdrant, pg = FakeProvider(), FakeAuthoritativeRepository()
    service = RetrievalQueryService(qdrant, pg, SimpleNamespace(settings=_settings()))
    payload = {
        "chunk_id": str(chunk_id),
        "document_id": str(doc_id),
        "document_version_id": str(version_id),
        "deployment_scope": "internal",
        "domain": "research",
        "classification": "synthetic_unclassified",
        "published": True,
    }
    qdrant.points = [SimpleNamespace(payload=payload, score=0.97)]
    arguments = {
        "query": "پرسش ١٢",
        "vector": [1.0, 0, 0, 0],
        "principal_id": "synthetic-owner",
        "domain": "research",
        "allowed_document_ids": [doc_id],
    }
    assert asyncio.run(service.retrieve_synthetic_dense_async(**arguments)) == []
    assert len(pg.decisions) == 1
    assert pg.decisions[0]["principal_id"] == "synthetic-owner"
    assert pg.decisions[0]["candidates"][0].chunk_id == chunk_id
    assert qdrant.calls[0]["authorized_document_ids"] == [doc_id]
    assert qdrant.calls[0]["authorized_classifications"] == ["synthetic_unclassified"]

    # Tampered source/scope/published flags cannot be overlooked even when the
    # Qdrant adapter returned a candidate contrary to its mandatory filter.
    for key, value in (
        ("deployment_scope", "public"),
        ("domain", "religion"),
        ("classification", "secret"),
        ("published", False),
        ("document_id", str(uuid4())),
        ("chunk_id", "not-a-uuid"),
    ):
        qdrant.points = [SimpleNamespace(payload={**payload, key: value}, score=0.9)]
        previous = len(pg.decisions)
        with pytest.raises(RetrievalContractError):
            asyncio.run(service.retrieve_synthetic_dense_async(**arguments))
        assert len(pg.decisions) == previous

    with pytest.raises(RetrievalContractError):
        asyncio.run(service.retrieve_synthetic_dense_async(**{**arguments, "allowed_document_ids": []}))
    with pytest.raises(RetrievalContractError):
        asyncio.run(service.retrieve_synthetic_dense_async(**{**arguments, "principal_id": ""}))


def test_disabled_production_mode_fails_before_qdrant():
    settings = _settings()
    settings.environment = "production"

    class FakeProvider:
        async def search_async(self, *args, **kwargs):
            pytest.fail("Must not query provider in blocked environment")

    service = RetrievalQueryService(FakeProvider(), object(), SimpleNamespace(settings=settings))
    with pytest.raises(RetrievalContractError, match="phase08_not_enabled"):
        asyncio.run(
            service.retrieve_synthetic_dense_async(
                query="سلام",
                vector=[1.0],
                principal_id="someone",
                domain="research",
                allowed_document_ids=[uuid4()],
            )
        )
