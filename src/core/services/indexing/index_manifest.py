"""Phase07 immutable pre-publication manifest and vector-validation contracts.

This is not an authorization or publication gate: model choice, durable
approval, and atomic PostgreSQL visibility remain separate requirements.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID, uuid5


class IndexContractError(ValueError):
    """Invalid source/evidence contract; messages never include source content."""


@dataclass(frozen=True)
class IndexSourceChunk:
    id: UUID
    ordinal: int
    canonical_text: str
    checksum_sha256: str
    processor_version: str
    normalizer_version: str
    page_number: int | None
    source_start: int
    source_end: int


@dataclass(frozen=True)
class IndexManifest:
    id: UUID
    document_id: UUID
    version_id: UUID
    scope: str
    domain: str
    classification: str
    model_id: str
    model_revision: str
    embedding_dimension: int
    distance: str
    schema_version: int
    processor_version: str
    normalizer_version: str
    chunk_count: int
    chunk_ids: tuple[UUID, ...]
    canonical_checksum_sha256: str


@dataclass(frozen=True)
class ValidatedVector:
    chunk_id: UUID
    values: tuple[float, ...]


def _token(value: str) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 100
        and all(c.isascii() and (c.islower() or c.isdigit() or c in "_-.") for c in value)
    )


def build_index_manifest(
    *,
    document_id: UUID,
    version_id: UUID,
    scope: str,
    domain: str,
    classification: str,
    model_id: str,
    model_revision: str,
    dimension: int,
    distance: str,
    schema_version: int,
    chunks: Sequence[IndexSourceChunk],
) -> IndexManifest:
    """Validate complete source chunks before any Qdrant writes."""
    if not all(isinstance(v, UUID) for v in (document_id, version_id)):
        raise IndexContractError("invalid_source_identity")
    if (
        scope not in {"internal", "public"}
        or not all(_token(v) for v in (domain, classification, model_id, model_revision))
        or not isinstance(dimension, int)
        or not 1 <= dimension <= 65536
        or distance not in {"Cosine", "Dot", "Euclid"}
        or not isinstance(schema_version, int)
        or not 1 <= schema_version <= 100000
        or not 1 <= len(chunks) <= 4096
    ):
        raise IndexContractError("invalid_index_contract")
    seen: set[UUID] = set()
    versions: set[tuple[str, str]] = set()
    encoded_chunks: list[dict] = []
    for ordinal, chunk in enumerate(chunks):
        if (
            not isinstance(chunk, IndexSourceChunk)
            or not isinstance(chunk.id, UUID)
            or chunk.id in seen
            or chunk.ordinal != ordinal
            or not isinstance(chunk.canonical_text, str)
            or not chunk.canonical_text.strip()
            or len(chunk.canonical_text) > 4000
            or not _token(chunk.processor_version)
            or not _token(chunk.normalizer_version)
            or (chunk.page_number is not None and chunk.page_number < 1)
            or chunk.source_start < 0
            or chunk.source_end <= chunk.source_start
            or hashlib.sha256(chunk.canonical_text.encode("utf-8")).hexdigest() != chunk.checksum_sha256
        ):
            raise IndexContractError("invalid_chunk_evidence")
        versions.add((chunk.processor_version, chunk.normalizer_version))
        seen.add(chunk.id)
        encoded_chunks.append(
            {
                "id": str(chunk.id),
                "ordinal": ordinal,
                "checksum": chunk.checksum_sha256,
                "page": chunk.page_number,
                "start": chunk.source_start,
                "end": chunk.source_end,
            }
        )
    if len(versions) != 1:
        raise IndexContractError("mixed_processor_versions")
    processor_version, normalizer_version = next(iter(versions))
    metadata = {
        "document_id": str(document_id),
        "version_id": str(version_id),
        "scope": scope,
        "domain": domain,
        "classification": classification,
        "model_id": model_id,
        "model_revision": model_revision,
        "dimension": dimension,
        "distance": distance,
        "schema_version": schema_version,
        "processor_version": processor_version,
        "normalizer_version": normalizer_version,
        "chunks": encoded_chunks,
    }
    encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return IndexManifest(
        id=uuid5(version_id, digest),
        document_id=document_id,
        version_id=version_id,
        scope=scope,
        domain=domain,
        classification=classification,
        model_id=model_id,
        model_revision=model_revision,
        embedding_dimension=dimension,
        distance=distance,
        schema_version=schema_version,
        processor_version=processor_version,
        normalizer_version=normalizer_version,
        chunk_count=len(chunks),
        chunk_ids=tuple(chunk.id for chunk in chunks),
        canonical_checksum_sha256=digest,
    )


def validate_embedding_vectors(
    manifest: IndexManifest, vectors: Sequence[Sequence[float]]
) -> tuple[ValidatedVector, ...]:
    """Reject incomplete, wrong-dimension, nonfinite and zero-cosine embeddings."""
    if not isinstance(manifest, IndexManifest) or len(vectors) != manifest.chunk_count:
        raise IndexContractError("embedding_count_mismatch")
    checked: list[ValidatedVector] = []
    for chunk_id, vector in zip(manifest.chunk_ids, vectors, strict=True):
        if isinstance(vector, (str, bytes)) or len(vector) != manifest.embedding_dimension:
            raise IndexContractError("embedding_dimension_mismatch")
        try:
            values = tuple(float(x) for x in vector)
        except (TypeError, ValueError, OverflowError):
            raise IndexContractError("invalid_embedding") from None
        if not all(math.isfinite(value) for value in values):
            raise IndexContractError("invalid_embedding")
        if manifest.distance == "Cosine" and not any(value != 0.0 for value in values):
            raise IndexContractError("zero_cosine_embedding")
        checked.append(ValidatedVector(chunk_id=chunk_id, values=values))
    return tuple(checked)
