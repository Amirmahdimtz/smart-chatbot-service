"""Deterministic, dependency-free validation of Phase 01 contracts."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "docs/requirements/requirements_contract.json"
ARCHITECTURE = ROOT / "docs/architecture/architecture_contract.json"
REQUIRED_CASES = {"UC-REL", "UC-HR-1", "UC-HR-2", "UC-HR-3", "UC-RES", "UC-DEV", "UC-TASK"}
REQUIRED_FILES = {
    "README.md",
    "docs/architecture/system_architecture.md",
    "docs/architecture/deployment_architecture.md",
    "docs/security/data_access_matrix.md",
    "docs/evaluation/evaluation_plan.md",
    "docs/implementation/progress.md",
    "docs/implementation/repository_discovery.md",
    "docs/implementation/phase_01_evidence.md",
    "docs/decisions/ADR-0001-architecture-baseline.md",
    "docs/decisions/ADR-0002-initialization-workflow.md",
}
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def validate() -> dict[str, int]:
    req = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    arch = json.loads(ARCHITECTURE.read_text(encoding="utf-8"))
    assert req["status"] == "PROPOSED_AWAITING_APPROVAL"
    assert arch["status"] == "PROPOSED_AWAITING_ARCHITECTURE_AND_SECURITY_APPROVAL"
    assert {s["id"] for s in req["scenarios"]} == REQUIRED_CASES
    policy_ids = {p["id"] for p in req["security_policies"]}
    assert policy_ids == set(arch["security"]["policy_ids"])
    assert "SEC-01" in policy_ids and "SEC-07" in policy_ids
    rows = req["requirements"]
    trace = req["traceability"]
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == len(trace)
    assert len({r["test_id"] for r in rows}) == len(rows)
    trace_by_id = {row["requirement_id"]: row for row in trace}
    assert set(trace_by_id) == set(ids)
    scenario_reqs = {
        r["id"]: (scenario, r)
        for scenario in req["scenarios"]
        for r in scenario["functional_requirements"]
    }
    assert set(scenario_reqs) == set(ids)
    for requirement in rows:
        rid = requirement["id"]
        scenario, compact = scenario_reqs[rid]
        tr = trace_by_id[rid]
        for name in ("feature", "data_refs", "security_policy_id", "test_id", "phase", "owner"):
            expected = requirement[name]
            observed = tr["data"] if name == "data_refs" else tr[name]
            assert observed == expected, f"{rid} mismatch in {name}"
        assert compact["test_id"] == requirement["test_id"]
        assert compact["security_policy_id"] == requirement["security_policy_id"]
        assert requirement["feature"] == scenario["feature"]
        assert requirement["phase"] == scenario["implementation_phase"]
        assert requirement["owner"] == scenario["approval_owner"]
        assert requirement["security_policy_id"] in policy_ids
        assert requirement["approval_status"] == "AWAITING_DOMAIN_APPROVAL"
    for s in req["scenarios"]:
        for key in ("actors", "roles", "data_requirements", "knowledge_sources",
                    "authorization_boundaries", "workflow", "external_dependencies",
                    "failure_scenarios", "acceptance_criteria", "test_strategy"):
            assert s[key], f"{s['id']} missing {key}"
        assert set(s["authorization_boundaries"]).issubset(policy_ids)
    assert arch["platform"]["persistence"] == "PostgreSQL"
    assert arch["platform"]["retrieval_index"] == "Qdrant"
    assert arch["platform"]["pgvector_permitted"] is False
    assert arch["platform"]["layers"] == ["Host", "Application", "Core", "Infrastructure"]
    assert arch["agent_integration"]["status"] == "BLOCKED_EXTERNAL_NOT_IMPLEMENTED"
    assert arch["agent_integration"]["endpoints"] == []
    assert all(route["status"] == "CANDIDATE_NOT_IMPLEMENTED" for route in arch["api_boundaries"])
    decisions = arch["open_decisions"]
    assert len({decision["id"] for decision in decisions}) == len(decisions) >= 16
    assert all(d["status"] == "OPEN" and d["decision_criteria"] and d["proposed_owner"]
               and d["affected_phases"] and d["evidence_required"] for d in decisions)
    for path in REQUIRED_FILES:
        assert (ROOT / path).is_file(), f"Missing required file: {path}"
    md_count = 0
    for document in (ROOT / "docs").rglob("*.md"):
        md_count += 1
        for target in LINK.findall(document.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (document.parent / target.split("#", 1)[0]).resolve()
            assert resolved.is_relative_to(ROOT.resolve()), f"Escaping reference: {document}: {target}"
            assert resolved.is_file(), f"Broken link: {document}: {target}"
    return {"scenarios": len(req["scenarios"]), "requirements": len(rows),
            "policies": len(policy_ids), "open_decisions": len(decisions),
            "linked_markdown_files": md_count}


if __name__ == "__main__":
    stats = validate()
    print("PHASE_01_CONTRACT_VALIDATION_OK", json.dumps(stats, sort_keys=True))

