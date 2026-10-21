"""Dependency-free integrity and acceptance-gate validation for Phase 01."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "docs/requirements/requirements_contract.json"
ARCHITECTURE = ROOT / "docs/architecture/architecture_contract.json"
ACCEPTANCE = ROOT / "docs/implementation/phase_01_acceptance.json"
REQUIRED_CASES = {"UC-REL", "UC-HR-1", "UC-HR-2", "UC-HR-3", "UC-RES", "UC-DEV", "UC-TASK"}
REQUIRED_FILES = {
    "README.md",
    "docs/requirements/requirements_contract.json",
    "docs/architecture/architecture_contract.json",
    "docs/architecture/system_architecture.md",
    "docs/architecture/deployment_architecture.md",
    "docs/security/data_access_matrix.md",
    "docs/evaluation/evaluation_plan.md",
    "docs/implementation/progress.md",
    "docs/implementation/repository_discovery.md",
    "docs/implementation/phase_01_evidence.md",
    "docs/implementation/phase_01_acceptance.json",
    "docs/implementation/approval_workflow.md",
    "docs/requirements/source_inventory.md",
    "docs/decisions/ADR-0001-architecture-baseline.md",
    "docs/decisions/ADR-0002-initialization-workflow.md",
    "docs/decisions/ADR-0003-acceptance-governance.md",
}
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
AWAITING = "IMPLEMENTED_AWAITING_VERIFICATION"
COMPLETE = "PHASE_01_COMPLETE_READY_FOR_PHASE_02"
PENDING_REQ = "PROPOSED_AWAITING_APPROVAL"
PENDING_ARCH = "PROPOSED_AWAITING_ARCHITECTURE_AND_SECURITY_APPROVAL"


class ContractValidationError(ValueError):
    """A contract invariant or approval gate was violated."""


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ContractValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContractValidationError(f"Cannot read valid JSON: {path}") from exc
    ensure(isinstance(content, dict), f"Expected JSON object: {path}")
    return content


def unique_index(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    ensure(isinstance(items, list), f"Invalid list of {key}")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        ensure(isinstance(item, dict) and isinstance(item.get(key), str) and bool(item[key]),
               f"Invalid entry with {key}")
        ensure(item[key] not in result, f"Duplicate {key}: {item[key]}")
        result[item[key]] = item
    return result


def _valid_evidence(root: Path, ref: Any) -> bool:
    if not isinstance(ref, str) or not ref or ref.startswith(("/", "\\")):
        return False
    candidate = (root / ref).resolve()
    return candidate.is_relative_to(root.resolve()) and candidate.is_file()


def validate(root: Path = ROOT) -> dict[str, int]:
    """Validate actual contracts and fail closed on inconsistent closure evidence."""
    root = root.resolve()
    req = load_json(root / "docs/requirements/requirements_contract.json")
    arch = load_json(root / "docs/architecture/architecture_contract.json")
    acceptance = load_json(root / "docs/implementation/phase_01_acceptance.json")

    scenarios = unique_index(req["scenarios"], "id")
    ensure(set(scenarios) == REQUIRED_CASES, "Seven mandatory use cases not fully covered")
    requirements = unique_index(req["requirements"], "id")
    traces = unique_index(req["traceability"], "requirement_id")
    ensure(len(requirements) >= 21 and set(requirements) == set(traces),
           "Requirements and trace IDs diverge")
    ensure(len({r["test_id"] for r in requirements.values()}) == len(requirements),
           "Duplicate test IDs")
    policies = unique_index(req["security_policies"], "id")
    ensure(set(policies) == set(arch["security"]["policy_ids"]), "Security policies diverge")
    ensure({"SEC-01", "SEC-02", "SEC-07", "SEC-08"}.issubset(policies),
           "Mandatory isolation and Agent policies missing")

    scenario_reqs: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for scenario in scenarios.values():
        ensure(scenario.get("status") in ("PROPOSED_AWAITING_APPROVAL", "APPROVED"),
               f"Invalid scenario status {scenario['id']}")
        for key in ("actors", "roles", "data_requirements", "knowledge_sources",
                    "authorization_boundaries", "workflow", "external_dependencies",
                    "failure_scenarios", "acceptance_criteria", "test_strategy", "approval_owner"):
            ensure(bool(scenario.get(key)), f"Scenario {scenario['id']} missing {key}")
        ensure(set(scenario["authorization_boundaries"]).issubset(policies),
               f"Unknown policy in {scenario['id']}")
        for item in scenario["functional_requirements"]:
            rid = item["id"]
            ensure(rid not in scenario_reqs, f"Duplicated scenario requirement {rid}")
            scenario_reqs[rid] = (scenario, item)
    ensure(set(scenario_reqs) == set(requirements), "Scenario requirements do not match global requirements")

    for rid, item in requirements.items():
        scenario, compact = scenario_reqs[rid]
        trace = traces[rid]
        for key in ("feature", "security_policy_id", "test_id", "phase", "owner"):
            ensure(trace[key] == item[key], f"Traceability mismatch {rid}: {key}")
        ensure(trace["data"] == item["data_refs"], f"Traceability mismatch {rid}: data")
        ensure(item["security_policy_id"] in policies, f"Unknown policy for {rid}")
        ensure(item["feature"] == scenario["feature"], f"Wrong feature for {rid}")
        ensure(item["owner"] == scenario["approval_owner"], f"Wrong owner for {rid}")
        ensure(item["phase"] == scenario["implementation_phase"], f"Wrong phase for {rid}")
        ensure(compact["test_id"] == item["test_id"], f"Test ID mismatch {rid}")
        ensure(compact["security_policy_id"] == item["security_policy_id"],
               f"Policy ID mismatch {rid}")
        ensure(item["approval_status"] in ("AWAITING_DOMAIN_APPROVAL", "APPROVED"),
               f"Invalid requirement approval state {rid}")

    platform = arch["platform"]
    ensure(platform["layers"] == ["Host", "Application", "Core", "Infrastructure"],
           "Wrong application layers")
    ensure(platform["persistence"] == "PostgreSQL" and
           platform["retrieval_index"] == "Qdrant" and
           platform["pgvector_permitted"] is False, "Incorrect persistence boundary")
    ensure(arch["agent_integration"]["status"] == "BLOCKED_EXTERNAL_NOT_IMPLEMENTED" and
           arch["agent_integration"]["endpoints"] == [], "External Agent incorrectly declared ready")
    ensure(all(route["status"] == "CANDIDATE_NOT_IMPLEMENTED"
               for route in arch["api_boundaries"]), "Nonexistent API claimed as implemented")

    decisions = unique_index(arch["open_decisions"], "id")
    ensure(len(decisions) >= 20, "Missing documented open decisions")
    for decision in decisions.values():
        ensure(decision["status"] in ("OPEN", "ACCEPTED", "DEFERRED_APPROVED"),
               f"Invalid decision state {decision['id']}")
        ensure(bool(decision["proposed_owner"] and decision["decision_criteria"]
                    and decision["affected_phases"] and decision["evidence_required"]),
               f"Incomplete decision criteria {decision['id']}")
        ensure(isinstance(decision.get("due_milestone"), str) and decision["due_milestone"],
               f"Missing milestone deadline {decision['id']}")
        ensure(decision.get("owner_confirmed") is True or
               decision.get("owner_confirmed") is False,
               f"Missing confirmation status {decision['id']}")
        if decision["status"] != "OPEN":
            ensure(decision["owner_confirmed"] is True and
                   _valid_evidence(root, decision.get("decision_evidence_ref")),
                   f"Accepted decision needs verified approval record {decision['id']}")

    ensure(acceptance.get("phase") == "PHASE_01", "Wrong phase acceptance record")
    gates = unique_index(acceptance["gates"], "id")
    ensure({"G-01", "G-02", "G-03", "G-04", "G-05", "G-06", "G-07", "G-08"}.issubset(gates),
           "Mandatory phase acceptance gates missing")
    for gate in gates.values():
        ensure(bool(gate.get("owner_role")) and bool(gate.get("description")),
               f"Gate missing accountable role {gate['id']}")
        ensure(gate["status"] in ("AWAITING_APPROVAL", "AWAITING_INPUT", "AWAITING_DECISION",
                                  "RECHECK_REQUIRED", "APPROVED", "VERIFIED"),
               f"Invalid gate state {gate['id']}")
        if gate["status"] in ("APPROVED", "VERIFIED"):
            ensure(_valid_evidence(root, gate.get("evidence_ref")) and
                   isinstance(gate.get("approved_by"), str) and bool(gate["approved_by"].strip()) and
                   isinstance(gate.get("approved_at"), str) and bool(gate["approved_at"].strip()),
                   f"No attributable review evidence for {gate['id']}")

    req_status, arch_status = req["status"], arch["status"]
    ensure(req_status in (PENDING_REQ, "APPROVED") and
           arch_status in (PENDING_ARCH, "APPROVED"), "Invalid contract state")
    progress = (root / "docs/implementation/progress.md").read_text(encoding="utf-8")
    declared_status = acceptance.get("phase_status")
    ensure(declared_status in (AWAITING, "CLOSED"), "Invalid phase status in acceptance record")
    ensure(f"**Status After:** {declared_status}" in progress,
           "Progress status does not match acceptance status")
    expected_marker = COMPLETE if declared_status == "CLOSED" else "PHASE_01_IMPLEMENTED_AWAITING_VERIFICATION"
    ensure(f"**Marker:** {expected_marker}" in progress, "Phase marker does not match status")
    ensure(bool(re.search(rf"^\|\s*01\s*\|\s*{re.escape(declared_status)}\s*\|", progress, re.MULTILINE)),
           "Phase 01 summary table does not match acceptance status")
    if declared_status == "CLOSED":
        ensure(all(d["owner_confirmed"] is True for d in decisions.values()),
               "Open decision ownership has not been confirmed")
        ensure(req_status == arch_status == "APPROVED", "Contracts not approved")
        ensure(all(v == "APPROVED" for v in req["approval"].values()) and
               all(v == "APPROVED" for v in arch["approval"].values()),
               "Product/architecture/security approvals missing")
        ensure(all(r["approval_status"] == "APPROVED" for r in requirements.values()) and
               all(s["status"] == "APPROVED" for s in scenarios.values()),
               "Domain sign-off incomplete")
        ensure(all(g["status"] in ("APPROVED", "VERIFIED") for g in gates.values()),
               "Acceptance gates incomplete")
    else:
        ensure(req_status == PENDING_REQ and arch_status == PENDING_ARCH,
               "Pending phase contains inconsistent contract status")

    for path in REQUIRED_FILES:
        ensure((root / path).is_file(), f"Required file missing: {path}")
    md_count = 0
    for doc in (root / "docs").rglob("*.md"):
        md_count += 1
        for link in LINK.findall(doc.read_text(encoding="utf-8")):
            target = unquote(link.split("#", 1)[0])
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            ensure(not target.startswith("/"), f"Absolute local reference: {doc}: {target}")
            resolved = (doc.parent / target).resolve()
            ensure(resolved.is_relative_to(root) and resolved.is_file(),
                   f"Invalid document link: {doc}: {target}")
    return {"scenarios": len(scenarios), "requirements": len(requirements),
            "policies": len(policies), "open_decisions": len(decisions),
            "linked_markdown_files": md_count, "acceptance_gates": len(gates)}


if __name__ == "__main__":
    try:
        result = validate()
    except (ContractValidationError, KeyError, TypeError, OSError) as exc:
        raise SystemExit(f"PHASE_01_CONTRACT_VALIDATION_FAILED: {exc}") from exc
    print("PHASE_01_CONTRACT_VALIDATION_OK", json.dumps(result, sort_keys=True))
