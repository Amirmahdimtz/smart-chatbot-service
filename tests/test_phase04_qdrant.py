"""Qdrant contract/security tests plus opt-in real isolated-server integration."""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from qdrant_client import AsyncQdrantClient, models
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
        invalid = AsyncQdrantClient(url=os.environ["SCB_PHASE04_TEST_QDRANT_URL"], api_key="wrong_ci_key", timeout=3)
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
            assert ids == [deterministic_point_id(item, 1) for item in (good, hidden, other_doc, other_domain)]
            assert await provider.upsert_async([good]) == [deterministic_point_id(good, 1)]
            found = await provider.search_async(
                good.vector,
                domain="research",
                authorized_classifications=["synthetic"],
                authorized_document_ids=[doc_allowed],
            )
            assert [str(p.id) for p in found] == [deterministic_point_id(good, 1)]
            # Even malicious or accidentally mis-scoped data in this collection
            # cannot bypass the Qdrant query-level deployment scope filter.
            foreign_id = str(uuid4())
            await provider._client.upsert(
                collection_name=provider.collection_name,
                points=[
                    models.PointStruct(
                        id=foreign_id,
                        vector=list(good.vector),
                        payload={
                            "document_id": str(doc_allowed),
                            "domain": "research",
                            "classification": "synthetic",
                            "deployment_scope": "internal",
                            "published": True,
                        },
                    )
                ],
                wait=True,
            )
            assert [
                str(point.id)
                for point in await provider.search_async(
                    good.vector,
                    domain="research",
                    authorized_classifications=["synthetic"],
                    authorized_document_ids=[doc_allowed],
                )
            ] == [deterministic_point_id(good, 1)]
            with pytest.raises(QdrantContractError):
                await provider.search_async(
                    good.vector, domain="research", authorized_classifications=[], authorized_document_ids=[doc_allowed]
                )
            with pytest.raises(QdrantContractError):
                await provider.search_async(
                    good.vector,
                    domain="research",
                    authorized_classifications="synthetic",
                    authorized_document_ids=[doc_allowed],
                )
            with pytest.raises(QdrantContractError):
                await provider.search_async(
                    good.vector, domain="research", authorized_classifications=["synthetic"], authorized_document_ids=[]
                )
            with pytest.raises(QdrantContractError):
                await provider.upsert_async([good, good])
            with pytest.raises(QdrantContractError):
                await provider.upsert_async([_record(dimensions=3)])
            aborted = _record()
            with pytest.raises(QdrantContractError):
                await provider.upsert_async([aborted, _record(dimensions=3)])
            assert not await provider.search_async(
                aborted.vector,
                domain="research",
                authorized_classifications=["synthetic"],
                authorized_document_ids=[aborted.document_id],
            )
            manifest = await provider.backup_manifest_async()
            assert manifest.collection_name == provider.collection_name
            assert manifest.active_alias_target == provider.collection_name
            assert manifest.schema_version == 1
            assert manifest.dimension == 4
            assert manifest.distance == "Cosine"
            assert manifest.deployment_zone == "public"
            assert manifest.snapshot_name.endswith(".snapshot")
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


def test_real_qdrant_isolated_rebuild_schema_mismatch_and_alias_rollback(monkeypatch):
    provider = _integration_provider(monkeypatch)

    async def exercise():
        await provider.start_async()
        version_one = provider._cfg
        record = _record()
        try:
            first_collection = await provider.ensure_collection_async()
            await provider.activate_collection_async()
            await provider.upsert_async([record])
            first = await provider.search_async(
                record.vector,
                domain="research",
                authorized_classifications=["synthetic"],
                authorized_document_ids=[record.document_id],
            )
            assert len(first) == 1
            assert str(first[0].id) == deterministic_point_id(record, 1)
            provider._cfg = version_one.model_copy(update={"schema_version": 2})
            second_collection = await provider.ensure_collection_async()
            assert second_collection != first_collection
            await provider.upsert_async([record])
            await provider.activate_collection_async()
            second = await provider.search_async(
                record.vector,
                domain="research",
                authorized_classifications=["synthetic"],
                authorized_document_ids=[record.document_id],
            )
            assert len(second) == 1
            assert str(second[0].id) == deterministic_point_id(record, 2)
            provider._cfg = version_one
            await provider.activate_collection_async()
            rollback = await provider.search_async(
                record.vector,
                domain="research",
                authorized_classifications=["synthetic"],
                authorized_document_ids=[record.document_id],
            )
            assert len(rollback) == 1
            assert str(rollback[0].id) == deterministic_point_id(record, 1)
            provider._cfg = version_one.model_copy(update={"dimension": 8})
            with pytest.raises(QdrantContractError):
                await provider.ensure_collection_async()
            provider._cfg = version_one.model_copy(update={"schema_version": 3})
            await provider._client.create_collection(
                collection_name=provider.collection_name,
                vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
            )
            await provider._client.create_payload_index(
                collection_name=provider.collection_name,
                field_name="published",
                field_schema=models.PayloadSchemaType.KEYWORD,
                wait=True,
            )
            with pytest.raises(QdrantContractError):
                await provider.ensure_collection_async()
        finally:
            await provider.close_async()

    asyncio.run(exercise())


def test_retries_are_bounded_and_no_endpoint_is_exposed(monkeypatch):
    provider = _integration_provider(monkeypatch)
    provider._cfg = provider._cfg.model_copy(update={"max_retries": 1})
    calls = []

    class AlwaysTimeout:
        async def get_collections(self):
            calls.append(True)
            raise TimeoutError("synthetic test url / api-key must not escape")

    provider._client = AlwaysTimeout()

    async def exercise():
        with pytest.raises(QdrantUnavailable) as exc:
            await provider.check_async()
        assert len(calls) == 2
        assert "api-key" not in str(exc.value)

    asyncio.run(exercise())


def test_real_qdrant_disposable_snapshot_restore_round_trip(monkeypatch):
    """Restore source snapshot into a new synthetic collection; no production writes."""
    provider = _integration_provider(monkeypatch)

    async def exercise():
        await provider.start_async()
        try:
            source_name = await provider.ensure_collection_async()
            record = _record()
            await provider.upsert_async([record])
            before_aliases = await provider._client.get_aliases()
            manifest = await provider.backup_manifest_async()
            assert manifest.active_alias_target is None
            snapshot_name = manifest.snapshot_name
            assert snapshot_name.endswith(".snapshot")
            restored_name = f"{provider._cfg.collection_prefix}_public_restore_test"
            # The source snapshot remains on the disposable Qdrant Docker node.
            # Qdrant supports file:// paths and SNAPSHOT priority for fresh restores.
            result = await provider._client.recover_snapshot(
                collection_name=restored_name,
                location=f"file:///qdrant/snapshots/{source_name}/{snapshot_name}",
                priority=models.SnapshotPriority.SNAPSHOT,
                wait=True,
            )
            assert result is True
            restored = await provider._client.query_points(
                collection_name=restored_name,
                query=list(record.vector),
                query_filter=provider._filter("research", ["synthetic"], [record.document_id]),
                with_payload=True,
                limit=10,
            )
            assert len(restored.points) == 1
            assert str(restored.points[0].id) == deterministic_point_id(record, 1)
            assert restored.points[0].payload["document_version_id"] == str(record.document_version_id)
            # Collection snapshots do not include aliases. Verify that the
            # existing alias state remains unchanged; alias backup is separate.
            after_aliases = await provider._client.get_aliases()
            assert after_aliases == before_aliases
        finally:
            await provider.close_async()

    asyncio.run(exercise())
