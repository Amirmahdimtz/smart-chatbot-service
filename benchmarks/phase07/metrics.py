"""Deterministic, dependency-free metrics for Phase07 synthetic retrieval evaluation.

Scores are calculated only from explicit query relevance labels, without
inferring acceptance thresholds or treating out-of-scope documents as relevant.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path


def load_dataset(path: Path) -> tuple[dict, str]:
    payload = path.read_bytes()
    dataset = json.loads(payload)
    if not isinstance(dataset, dict):
        raise ValueError("invalid_dataset")
    documents = dataset.get("documents")
    queries = dataset.get("queries")
    if (
        dataset.get("classification") != "synthetic_unclassified"
        or not isinstance(documents, list)
        or not isinstance(queries, list)
        or len(documents) < 2
        or len(queries) < 2
    ):
        raise ValueError("invalid_dataset")
    ids: set[str] = set()
    docs: dict[str, dict] = {}
    for doc in documents:
        if (
            not isinstance(doc, dict)
            or set(doc) != {"id", "domain", "scope", "text"}
            or not all(isinstance(doc[key], str) and doc[key] for key in doc)
            or doc["id"] in ids
            or doc["scope"] not in {"public", "internal"}
            or len(doc["text"]) > 4000
        ):
            raise ValueError("invalid_document")
        ids.add(doc["id"])
        docs[doc["id"]] = doc
    qids: set[str] = set()
    positive = 0
    for query in queries:
        if (
            not isinstance(query, dict)
            or not isinstance(query.get("id"), str)
            or query["id"] in qids
            or not isinstance(query.get("text"), str)
            or not query["text"].strip()
            or len(query["text"]) > 2048
            or not isinstance(query.get("relevant_ids"), list)
            or len(query["relevant_ids"]) != len(set(query["relevant_ids"]))
            or not isinstance(query.get("domain"), str)
            or query.get("authorized_scope") not in {"public", "internal"}
            or query.get("should_abstain") is not (len(query["relevant_ids"]) == 0)
        ):
            raise ValueError("invalid_query_labels")
        qids.add(query["id"])
        for rid in query["relevant_ids"]:
            doc = docs.get(rid)
            if (
                doc is None
                or doc["domain"] != query["domain"]
                or doc["scope"] != query["authorized_scope"]
            ):
                raise ValueError("cross_scope_or_unknown_relevant_id")
        positive += bool(query["relevant_ids"])
    if not positive:
        raise ValueError("no_evaluable_queries")
    return dataset, hashlib.sha256(payload).hexdigest()


def score_ranking(ranking: list[str], relevant: set[str]) -> dict[str, float]:
    if not relevant or len(ranking) != len(set(ranking)):
        raise ValueError("invalid_ranking_or_relevance")
    rr = 0.0
    dcg = 0.0
    for pos, doc_id in enumerate(ranking[:10], start=1):
        if doc_id in relevant:
            if not rr:
                rr = 1 / pos
            dcg += 1 / math.log2(pos + 1)
    ideal = sum(1 / math.log2(pos + 1) for pos in range(1, min(10, len(relevant)) + 1))
    return {
        "recall_at_1": len(set(ranking[:1]) & relevant) / len(relevant),
        "recall_at_3": len(set(ranking[:3]) & relevant) / len(relevant),
        "recall_at_5": len(set(ranking[:5]) & relevant) / len(relevant),
        "mrr_at_10": rr,
        "ndcg_at_10": dcg / ideal,
    }


def evaluate(
    dataset: Mapping,
    rankings: Mapping[str, list[str]],
) -> dict:
    docs = {d["id"]: d for d in dataset["documents"]}
    sums: dict[str, float] = {}
    by_category: dict[str, list[float]] = {}
    evaluable = 0
    excluded = 0
    for query in dataset["queries"]:
        found = rankings.get(query["id"])
        if found is None or not isinstance(found, list):
            raise ValueError("missing_query_result")
        valid_ids = {
            doc_id
            for doc_id, doc in docs.items()
            if doc["domain"] == query["domain"]
            and doc["scope"] == query["authorized_scope"]
        }
        if any(doc not in valid_ids for doc in found):
            raise ValueError("scope_filter_violation")
        if len(found) != len(set(found)):
            raise ValueError("duplicate_ranking")
        relevant = set(query["relevant_ids"])
        if not relevant:
            excluded += 1
            continue
        evaluable += 1
        scores = score_ranking(found, relevant)
        for key, value in scores.items():
            sums[key] = sums.get(key, 0.0) + value
        by_category.setdefault(query["category"], []).append(scores["recall_at_1"])
    return {
        "metrics": {key: round(value / evaluable, 6) for key, value in sorted(sums.items())},
        "evaluated_queries": evaluable,
        "no_relevant_queries_not_scored": excluded,
        "recall_at_1_by_category": {
            key: round(sum(values) / len(values), 6)
            for key, values in sorted(by_category.items())
        },
        "no_relevant_query_abstention_evaluated": False,
    }
