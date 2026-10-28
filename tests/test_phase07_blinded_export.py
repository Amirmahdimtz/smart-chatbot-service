"""Group A: blind review cannot receive author proposed relevance or approval."""

import json
from pathlib import Path

from benchmarks.phase07.export_blinded_review import build_blinded_packet


def test_blinded_export_removes_every_synthetic_proposal_and_keeps_source_hashes():
    seed = json.loads(Path("benchmarks/phase07/gold_synthetic_v0.1.json").read_text(encoding="utf-8"))
    packet = build_blinded_packet(seed)
    assert packet["status"] == "BLINDED_REVIEW_CANDIDATE_NOT_GOLD"
    assert packet["approval"] is None
    assert len(packet["entries"]) == len(seed["queries"]) == 20
    raw = json.dumps(packet)
    assert '"relevant_ids"' not in raw
    assert '"proposed_relevance"' not in raw
    assert '"should_abstain"' not in raw
    assert all(
        row["reviewer_A"] is None
        and row["reviewer_B"] is None
        and row["adjudicator"] is None
        and row["final_relevant_ids"] is None
        and len(row["query_sha256"]) == 64
        and len(row["candidate_sources"]) > 0
        and all(len(d["document_sha256"]) == 64 for d in row["candidate_sources"])
        for row in packet["entries"]
    )
