"""Phase08 conservative deterministic evidence-budget and abstention hints.

These are structural protections, NOT learned relevance/evidence-sufficiency
judgements and not a substitute for an approved reranker or D-12 benchmark.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from uuid import UUID

from src.core.services.retrieval.retrieval_contract import RetrievalContractError


@dataclass(frozen=True)
class EvidenceSlice:
    chunk_id: UUID
    version_id: UUID
    canonical: str
    checksum_sha256: str
    score: float


@dataclass(frozen=True)
class EvidenceWindow:
    selected: tuple[EvidenceSlice, ...]
    abstain_hint: str | None
    dropped_for_budget: int


def select_evidence_window(
    evidence: list[EvidenceSlice],
    *,
    max_evidence_chars: int = 6000,
    max_chunks: int = 8,
) -> EvidenceWindow:
    """No truncation, no invented citations and stable input-rank ordering.

    The caller must already have run authoritative source/permission checks.
    None of these decisions means a model can ground its proposed answer.
    """
    if (
        not isinstance(evidence, list)
        or len(evidence) > 100
        or not isinstance(max_evidence_chars, int)
        or not 256 <= max_evidence_chars <= 100_000
        or not isinstance(max_chunks, int)
        or not 1 <= max_chunks <= 100
    ):
        raise RetrievalContractError("invalid_evidence_budget")
    seen: dict[UUID, tuple[UUID, str]] = {}
    selected: list[EvidenceSlice] = []
    used = 0
    dropped = 0
    for item in evidence:
        if (
            not isinstance(item, EvidenceSlice)
            or not isinstance(item.chunk_id, UUID)
            or not isinstance(item.version_id, UUID)
            or not isinstance(item.canonical, str)
            or not item.canonical.strip()
            or not isinstance(item.checksum_sha256, str)
            or hashlib.sha256(item.canonical.encode("utf-8")).hexdigest() != item.checksum_sha256
            or not isinstance(item.score, (float, int))
            or not math.isfinite(item.score)
        ):
            raise RetrievalContractError("invalid_evidence")
        provenance = (item.version_id, item.checksum_sha256)
        if item.chunk_id in seen:
            if seen[item.chunk_id] != provenance:
                raise RetrievalContractError("conflicting_evidence")
            continue
        seen[item.chunk_id] = provenance
        if len(selected) == max_chunks or used + len(item.canonical) > max_evidence_chars:
            dropped += 1
            continue
        used += len(item.canonical)
        selected.append(item)
    if not selected:
        return EvidenceWindow((), "no_authorized_evidence" if not evidence else "evidence_over_budget", dropped)
    return EvidenceWindow(tuple(selected), None, dropped)
