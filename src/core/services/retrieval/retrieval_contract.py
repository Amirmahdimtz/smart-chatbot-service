"""Phase08 query and fusion contracts. Neither ranks nor Qdrant payloads confer access.

No model selection, lexical strategy or Reranker approval is implied by RRF.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from uuid import UUID

from src.core.services.persian_text.persian_processing import normalize_persian


class RetrievalContractError(ValueError):
    def __init__(self, code: str = "invalid_retrieval_contract"):
        super().__init__(code)


@dataclass(frozen=True)
class CandidateHit:
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    score: float


@dataclass(frozen=True)
class FusedCandidate:
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    rrf_score: float
    channels: tuple[str, ...]


def normalize_query(raw: str, *, max_chars: int = 2048) -> str:
    """Reuse Phase06 Persian normalization, never mutate stored chunk text."""
    if (
        not isinstance(raw, str)
        or not 1 <= max_chars <= 8192
        or not 1 <= len(raw) <= max_chars
        or any(ord(c) < 32 and c not in "\t\n\r" for c in raw)
    ):
        raise RetrievalContractError("invalid_query")
    canonical = normalize_persian(raw)
    if not canonical:
        raise RetrievalContractError("empty_query")
    return canonical


def fuse_rrf(
    dense: list[CandidateHit],
    lexical: list[CandidateHit],
    *,
    rank_constant: int,
    limit: int,
) -> list[FusedCandidate]:
    """Configurable Reciprocal Rank Fusion with stable deterministic tie breaks.

    Channels must be independently ranked by their provider. Conflicting chunk
    provenance from those channels aborts the entire set, not just the conflict.
    """
    if (
        not isinstance(rank_constant, int)
        or not 1 <= rank_constant <= 10000
        or not isinstance(limit, int)
        or not 1 <= limit <= 100
        or not isinstance(dense, list)
        or not isinstance(lexical, list)
        or len(dense) > 1000
        or len(lexical) > 1000
    ):
        raise RetrievalContractError()
    evidence: dict[UUID, tuple[UUID, UUID]] = {}
    totals: dict[UUID, float] = {}
    channel_sets: dict[UUID, set[str]] = {}
    for channel, hits in (("dense", dense), ("lexical", lexical)):
        seen: set[UUID] = set()
        for rank, hit in enumerate(hits, start=1):
            if (
                not isinstance(hit, CandidateHit)
                or not all(isinstance(v, UUID) for v in (hit.chunk_id, hit.document_id, hit.version_id))
                or not isinstance(hit.score, (int, float))
                or not math.isfinite(hit.score)
                or hit.chunk_id in seen
            ):
                raise RetrievalContractError("invalid_candidate")
            seen.add(hit.chunk_id)
            provenance = (hit.document_id, hit.version_id)
            if hit.chunk_id in evidence and evidence[hit.chunk_id] != provenance:
                raise RetrievalContractError("candidate_provenance_conflict")
            evidence[hit.chunk_id] = provenance
            totals[hit.chunk_id] = totals.get(hit.chunk_id, 0.0) + 1.0 / (rank_constant + rank)
            channel_sets.setdefault(hit.chunk_id, set()).add(channel)
    ordered = sorted(totals, key=lambda chunk_id: (-totals[chunk_id], str(chunk_id)))
    return [
        FusedCandidate(
            chunk_id=chunk_id,
            document_id=evidence[chunk_id][0],
            version_id=evidence[chunk_id][1],
            rrf_score=totals[chunk_id],
            channels=tuple(sorted(channel_sets[chunk_id])),
        )
        for chunk_id in ordered[:limit]
    ]
