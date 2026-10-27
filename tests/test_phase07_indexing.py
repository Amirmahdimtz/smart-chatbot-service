"""Phase07 Group A: deterministic index evidence and unpublished staging contracts."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.core.services.indexing.index_manifest import (
    IndexContractError,
    IndexSourceChunk,
    build_index_manifest,
    validate_embedding_vectors,
)
from src.infrastructure.providers.qdrant.index_staging_service import IndexStagingService


def _source(count=3):
    document_id, version_id = uuid4(), uuid4()
    chunks = []
    for ordinal in range(count):
        text = f"ماده {ordinal + 1}: متن آزمایشی مستند."
        chunks.append(
            IndexSourceChunk(
                id=uuid4(),
                ordinal=ordinal,
                canonical_text=text,
                checksum_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                processor_version="fa-structure-v1",
                normalizer_version="fa-nfc-normalizer-v1",
                page_number=ordinal // 2 + 1,
                source_start=0,
                source_end=len(text),
            )
        )
    arguments = {
        "document_id": document_id,
        "version_id": version_id,
        "scope": "internal",
        "domain": "research",
        "classification": "synthetic_unclassified",
        "model_id": "candidate_local_a",
        "model_revision": "candidate_revision_1",
        "dimension": 4,
        "distance": "Cosine",
        "schema_version": 1,
    }
    return arguments, chunks


def _manifest(count=3):
    arguments, chunks = _source(count)
    return build_index_manifest(**arguments, chunks=chunks)


def test_manifest_is_deterministic_but_changes_on_revisions():
    settings, chunks = _source()
    first = build_index_manifest(**settings, chunks=chunks)
    second = build_index_manifest(**settings, chunks=tuple(chunks))
    assert first == second
    assert first.chunk_count == len(chunks)
    assert first.chunk_ids == tuple(part.id for part in chunks)
    assert first.processor_version == "fa-structure-v1"
    changed = build_index_manifest(**{**settings, "model_revision": "candidate_revision_2"}, chunks=chunks)
    assert changed.id != first.id
    assert changed.canonical_checksum_sha256 != first.canonical_checksum_sha256
    newer = replace(chunks[1], canonical_text=chunks[1].canonical_text + " اصلاح")
    newer = replace(newer, checksum_sha256=hashlib.sha256(newer.canonical_text.encode()).hexdigest())
    assert build_index_manifest(**settings, chunks=[chunks[0], newer, chunks[2]]).id != first.id


@pytest.mark.parametrize(
    "modify",
    [
        lambda cs: [replace(cs[0], checksum_sha256="0" * 64), *cs[1:]],
        lambda cs: [cs[0], replace(cs[1], ordinal=0), cs[2]],
        lambda cs: [cs[0], replace(cs[1], id=cs[0].id), cs[2]],
        lambda cs: [cs[0], replace(cs[1], processor_version="other-v1"), cs[2]],
        lambda cs: [replace(cs[0], source_end=0), *cs[1:]],
        lambda cs: [replace(cs[0], canonical_text=""), *cs[1:]],
    ],
)
def test_invalid_source_evidence_fails_before_qdrant(modify):
    settings, chunks = _source()
    with pytest.raises(IndexContractError):
        build_index_manifest(**settings, chunks=modify(chunks))


def test_nonfinite_wrong_dim_partial_and_zero_cosine_fail_closed():
    manifest = _manifest()
    good = [[1, 0, 0, 0]] * manifest.chunk_count
    checked = validate_embedding_vectors(manifest, good)
    assert len(checked) == manifest.chunk_count
    assert all(v.chunk_id in manifest.chunk_ids for v in checked)
    for broken in (
        good[:-1],
        [[0, 0, 0]] + good[1:],
        [[float("nan"), 0, 0, 1]] + good[1:],
        [[float("inf"), 0, 0, 1]] + good[1:],
        [[0, 0, 0, 0]] + good[1:],
    ):
        with pytest.raises(IndexContractError):
            validate_embedding_vectors(manifest, broken)


def test_batched_unpublished_staging_and_duplicate_replay():
    manifest = _manifest(count=5)
    embeddings = validate_embedding_vectors(manifest, [[1, 0, 0, 0]] * 5)

    class QdrantStub:
        def __init__(self):
            self.records = []
            self.ensures = 0

        async def ensure_collection_async(self):
            self.ensures += 1

        async def upsert_async(self, rows):
            self.records.extend(rows)
            return [str(item.chunk_id) for item in rows]

    settings = SimpleNamespace(
        qdrant=SimpleNamespace(enabled=True, schema_version=1, dimension=4, distance="Cosine", batch_size=2),
        ingestion=SimpleNamespace(synthetic_only=True),
        environment="development",
        deployment_zone="internal",
    )
    fake = QdrantStub()
    service = IndexStagingService(fake, SimpleNamespace(settings=settings))
    first = asyncio.run(service.stage_async(manifest, embeddings))
    assert len(first) == 5
    assert all(row.published is False for row in fake.records)
    assert fake.ensures == 1
    assert first == asyncio.run(service.stage_async(manifest, embeddings))
    assert fake.ensures == 2
    wrong = replace(manifest, scope="public")
    before = len(fake.records)
    with pytest.raises(IndexContractError):
        asyncio.run(service.stage_async(wrong, embeddings))
    assert len(fake.records) == before
