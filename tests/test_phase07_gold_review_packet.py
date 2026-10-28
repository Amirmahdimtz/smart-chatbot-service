"""Group A: review packet cannot impersonate an approved Persian/Arabic Gold Set."""

from __future__ import annotations

import json
from pathlib import Path


def test_all_synthetic_questions_exported_for_blinded_review_without_fake_approval():
    seed = json.loads(Path("benchmarks/phase07/gold_synthetic_v0.1.json").read_text(encoding="utf-8"))
    packet = json.loads(Path("benchmarks/phase07/review_packet_v0.1.json").read_text(encoding="utf-8"))
    assert packet["status"] == "REVIEW_REQUIRED_NOT_GOLD"
    assert packet["final_acceptance"] is False
    assert packet["blind_annotation_required"] is True
    assert {item["query_id"] for item in packet["records"]} == {q["id"] for q in seed["queries"]}
    documents = {d["id"]: d for d in seed["documents"]}
    proposals = {q["id"]: q["relevant_ids"] for q in seed["queries"]}
    assert len(packet["records"]) == 20
    assert all(
        row["label_status"] == "UNREVIEWED_SYNTHETIC"
        and row["reviewer_A"] is None
        and row["reviewer_B"] is None
        and row["adjudicator"] is None
        and row["data_owner_approval"] is None
        and row["security_approval"] is None
        and row["proposed_relevance"] == proposals[row["query_id"]]
        and all(
            evidence["document_id"] in documents
            and evidence["preview"] == documents[evidence["document_id"]]["text"][:120]
            for evidence in row["proposed_evidence_snippets"]
        )
        for row in packet["records"]
    )
