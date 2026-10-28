"""Export reviewer-safe Persian/Arabic synthetic candidate questions.

Never copy pre-labeled synthetic relevance IDs into blind review assignments.
This script does NOT create an approved Gold corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def build_blinded_packet(seed: dict) -> dict:
    if seed.get("classification") != "synthetic_unclassified":
        raise ValueError("only_synthetic_seed_allowed")
    docs = seed["documents"]
    queries = seed["queries"]
    result = {
        "status": "BLINDED_REVIEW_CANDIDATE_NOT_GOLD",
        "version": "p07-blind-review-v1",
        "approval": None,
        "entries": [],
    }
    for query in queries:
        candidates = [
            {
                "id": d["id"],
                "text": d["text"],
                "document_sha256": hashlib.sha256(d["text"].encode("utf-8")).hexdigest(),
            }
            for d in docs
            if d["domain"] == query["domain"] and d["scope"] == query["authorized_scope"]
        ]
        if not candidates:
            raise ValueError("empty_blind_candidate_set")
        result["entries"].append(
            {
                "query_id": query["id"],
                "query_text": query["text"],
                "query_sha256": hashlib.sha256(query["text"].encode("utf-8")).hexdigest(),
                "domain": query["domain"],
                "authorized_scope": query["authorized_scope"],
                "candidate_sources": candidates,
                "reviewer_A": None,
                "reviewer_B": None,
                "adjudicator": None,
                "owner_approval": None,
                "security_approval": None,
                "final_relevant_ids": None,
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, default=Path("benchmarks/phase07/gold_synthetic_v0.1.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    packet = build_blinded_packet(seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
