"""Pure Phase08 structural evidence checks; no real-model quality claims."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from uuid import uuid4

import pytest

from src.core.services.retrieval.evidence_budget import EvidenceSlice, select_evidence_window
from src.core.services.retrieval.retrieval_contract import RetrievalContractError


def _sample(text: str, score: float = 0.8) -> EvidenceSlice:
    return EvidenceSlice(
        chunk_id=uuid4(),
        version_id=uuid4(),
        canonical=text,
        checksum_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        score=score,
    )


def test_no_evidence_abstains_and_budget_does_not_fabricate_citations():
    empty = select_evidence_window([])
    assert empty.abstain_hint == "no_authorized_evidence"
    assert empty.selected == ()
    long = _sample("دانش" * 200)
    rejected = select_evidence_window([long], max_evidence_chars=256)
    assert rejected.abstain_hint == "evidence_over_budget"
    assert rejected.dropped_for_budget == 1
    assert rejected.selected == ()


def test_ranked_evidence_window_deduplicates_and_never_truncates():
    a, b, c = _sample("الف " * 30), _sample("ب " * 30), _sample("ج " * 30)
    result = select_evidence_window([a, a, b, c], max_chunks=2)
    assert result.selected == (a, b)
    assert result.dropped_for_budget == 1
    assert result.abstain_hint is None
    assert result == select_evidence_window([a, a, b, c], max_chunks=2)


def test_source_checksum_and_provenance_conflicts_are_rejected():
    a = _sample("سلام")
    for broken in (
        replace(a, checksum_sha256="0" * 64),
        replace(a, score=float("nan")),
        replace(a, canonical=""),
    ):
        with pytest.raises(RetrievalContractError):
            select_evidence_window([broken])
    with pytest.raises(RetrievalContractError, match="conflicting_evidence"):
        select_evidence_window([a, replace(a, version_id=uuid4())])
