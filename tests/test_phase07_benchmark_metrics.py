"""Unit checks of benchmark scoring logic, not claims of model quality."""

from pathlib import Path

import pytest

from benchmarks.phase07.metrics import evaluate, load_dataset, score_ranking


def test_synthetic_fixture_integrity_and_authorization_scoping():
    data, checksum = load_dataset(Path("benchmarks/phase07/gold_synthetic_v0.1.json"))
    assert len(checksum) == 64
    assert len(data["documents"]) == 18
    assert len(data["queries"]) == 20
    assert sum(bool(q["relevant_ids"]) for q in data["queries"]) == 17
    rankings = {}
    for q in data["queries"]:
        rankings[q["id"]] = [
            d["id"]
            for d in data["documents"]
            if d["domain"] == q["domain"] and d["scope"] == q["authorized_scope"]
        ]
    result = evaluate(data, rankings)
    assert result["evaluated_queries"] == 17
    assert result["no_relevant_queries_not_scored"] == 3
    assert result["no_relevant_query_abstention_evaluated"] is False
    assert 0 <= result["metrics"]["recall_at_3"] <= 1


def test_ranking_metrics_are_exact_for_known_order_and_disjoint():
    score = score_ranking(["wrong", "correct", "other"], {"correct"})
    assert score["recall_at_1"] == 0.0
    assert score["recall_at_3"] == 1.0
    assert score["mrr_at_10"] == 0.5
    assert score["ndcg_at_10"] == pytest.approx(1 / 1.584962500721156)
    assert score_ranking(["wrong"], {"correct"})["mrr_at_10"] == 0.0
    with pytest.raises(ValueError):
        score_ranking(["x", "x"], {"x"})


def test_cross_scope_model_recommendations_are_never_scored():
    data, _ = load_dataset(Path("benchmarks/phase07/gold_synthetic_v0.1.json"))
    rankings = {q["id"]: [] for q in data["queries"]}
    rankings["Q01"] = ["H01"]
    with pytest.raises(ValueError, match="scope_filter_violation"):
        evaluate(data, rankings)
