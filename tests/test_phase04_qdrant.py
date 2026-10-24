"""Qdrant contract/security tests plus opt-in real isolated-server integration."""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.providers.qdrant.qdrant_provider import (
    QdrantContractError,
    QdrantProvider,
    QdrantUnavailable,
    VectorRecord,
    deterministic_point_id,
)
from src.infrastructure.utils.config_reader import ConfigReader, ConfigurationError


def _record(*, domain="research", published=True, document_id=None, dimensions=4):
    return VectorRecord(
        chunk_id=uuid4(),
        document_id=document_id or uuid4(),
        document_version_id=uuid4(),
        domain=domain,
        classification="synthetic",
        vector=[1.0] + [0.0] * (dimensions - 1),
        published=published,
    )


def test_qdrant_disabled_by_default_and_di(monkeypatch):
    monkeypatch.delenv("SCB_QDRANT_ENABLED", raising=False)
    container = bootstrap_di()
    assert not container.resolve(ConfigReader).settings.qdrant.enabled
    assert container.resolve(QdrantProvider) is container.resolve(QdrantProvider)
    async def exercise():
        provider = container.resolve(QdrantProvider)
        assert provider._client is None
        await provider.start_async()
        with pytest.raises(QdrantUnavailable):
            await provider.check_async()
        await provider.close_async()
    asyncio.run(exercise())


def test_qdrant_invalid_configuration_redacted(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.setenv("SCB_QDRANT_ENABLED", "true")
    monkeypatch.setenv("SCB_QDRANT_URL", "http://example.invalid")
    monkeypatch.setenv("SCB_QDRANT_API_KEY", "topsecret")
    monkeypatch.setenv("SCB_QDRANT_DIMENSION", "4")
    monkeypatch.setenv("SCB_QDRANT_ZONE", "internal")
    with pytest.raises(ConfigurationError) as exc:
        bootstrap_di().resolve(ConfigReader)
    assert "topsecret" not in str(exc.value)
    monkeypatch.setenv("SCB_QDRANT_ZONE", "public")
    monkeypatch.setenv("SCB_QDRANT_URL", "http://user:topsecret@127.0.0.1:6333")
    with pytest.raises(ConfigurationError):
        bootstrap_di().resolve(ConfigReader)
    monkeypatch.setenv("SCB_QDRANT_URL", "http://127.0.0.1:6333")
    monkeypatch.setenv("SCB_QDRANT_DIMENSION", "0")
    with pytest.raises(ConfigurationError):
        bootstrap_di().resolve(ConfigReader)
    monkeypatch.setenv("SCB_QDRANT_DIMENSION", "4")
    monkeypatch.setenv("SCB_QDRANT_ENABLED", "invalid")
    with pytest.raises(ConfigurationError):
        bootstrap_di().resolve(ConfigReader)


def test_point_identity_stability_and_input_validation():
    record = _record()
    assert deterministic_point_id(record, 1) == deterministic_point_id(record, 1)
    assert deterministic_point_id(record, 1) != deterministic_point_id(record, 2)
    other = _record()
    assert deterministic_point_id(record, 1) != deterministic_point_id(other, 1)


def _integration_provider(monkeypatch):
    url = os.environ.get("SCB_PHASE04_TEST_QDRANT_URL")
    if not url:
        pytest.skip("No disposable authenticated Qdrant test server configured")
    if url != "http://127.0.0.1:6333":
        pytest.fail("Refusing integration against non-isolated Qdrant host")
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.setenv("SCB_QDRANT_ENABLED", "true")
    monkeypatch.setenv("SCB_QDRANT_ZONE", "public")
    monkeypatch.setenv("SCB_QDRANT_URL", url)
    monkeypatch.setenv("SCB_QDRANT_API_KEY", os.environ["SCB_PHASE04_TEST_QDRANT_KEY"])
    monkeypatch.setenv("SCB_QDRANT_DIMENSION", "4")
    monkeypatch.setenv("SCB_QDRANT_COLLECTION_PREFIX", "scb_p04_" + uuid4().hex[:12])
    return bootstrap_di().resolve(QdrantProvider)


def test_real_qdrant_auth_schema_filter_alias_idempotence_snapshot(monkeypatch):
    provider = _integration_provider(monkeypatch)
    async def exercise():
        invalid = AsyncQdrantClient(
            url=os.environ["SCB_PHASE04_TEST_QDRANT_URL"], api_key="wrong_ci_key", timeout=3
        )
        try:
            with pytest.raises(UnexpectedResponse) as exc:
                await invalid.get_collections()
            assert exc.value.status_code in {401, 403}
        finally:
            await invalid.close()
        await provider.start_async()
        try:
            name = await provider.ensure_collection_async()
            assert name.endswith("_public_v1")
            await provider.activate_collection_async()
            await provider.activate_collection_async()
            doc_allowed = uuid4()
            doc_denied = uuid4()
            good = _record(document_id=doc_allowed)
            hidden = _record(document_id=doc_allowed, published=False)
            other_doc = _record(document_id=doc_denied)
            other_domain = _record(domain="religion", document_id=doc_allowed)
            ids = await provider.upsert_async([good, hidden, other_doc, other_domain])
            assert len(ids) == 4
            assert await provider.upsert_async([good]) == [deterministic_point_id(good, 1)]
            found = await provider.search_async(
                good.vector,
                domain="research",
                authorized_classifications=["synthetic"],
                authorized_document_ids=[doc_allowed],
            )
            assert [str(p.id) for p in found] == [deterministic_point_id(good, 1)]
            with pytest.raises(QdrantContractError):
                await provider.search_async(
                    good.vector, domain="research", authorized_classifications=[], authorized_document_ids=[doc_allowed]
                )
            with pytest.raises(QdrantContractError):
                await provider.search_async(
                    good.vector, domain="research", authorized_classifications=["synthetic"], authorized_document_ids=[]
                )
            with pytest.raises(QdrantContractError):
                await provider.upsert_async([good, good])
            with pytest.raises(QdrantContractError):
                await provider.upsert_async([_record(dimensions=3)])
            assert await provider.snapshot_async()
            await provider.delete_document_points_async(doc_allowed, domain="research")
            assert not await provider.search_async(
                good.vector,
                domain="research",
                authorized_classifications=["synthetic"],
                authorized_document_ids=[doc_allowed],
            )
            assert await provider.check_async()
        finally:
            await provider.close_async()
    asyncio.run(exercise())


def test_qdrant_unavailable_does_not_leak_endpoint(monkeypatch):
    provider = _integration_provider(monkeypatch)
    provider._cfg = provider._cfg.model_copy(update={"url": "http://127.0.0.1:1", "timeout_seconds": 0.3})
    async def exercise():
        with pytest.raises(QdrantUnavailable) as exc:
            await provider.start_async()
        assert "127.0.0.1" not in str(exc.value)
    asyncio.run(exercise())
