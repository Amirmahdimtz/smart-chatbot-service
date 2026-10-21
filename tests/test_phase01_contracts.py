"""Regression and deliberate corruption tests for Phase 01 contract gates."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_phase01 import (
    ARCHITECTURE, REQUIREMENTS, REQUIRED_CASES, ROOT,
    ContractValidationError, validate,
)


class Phase01ContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.req = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
        cls.arch = json.loads(ARCHITECTURE.read_text(encoding="utf-8"))

    def test_contract_validation_and_links(self) -> None:
        stats = validate()
        self.assertEqual(stats["scenarios"], 7)
        self.assertEqual(stats["requirements"], 21)
        self.assertEqual(stats["acceptance_gates"], 8)

    def test_every_domain_is_mapped(self) -> None:
        self.assertEqual({s["id"] for s in self.req["scenarios"]}, REQUIRED_CASES)
        self.assertEqual(len(self.req["traceability"]), len(self.req["requirements"]))

    def test_security_and_isolation_not_omitted(self) -> None:
        self.assertFalse(self.arch["platform"]["pgvector_permitted"])
        self.assertEqual(self.arch["platform"]["retrieval_index"], "Qdrant")
        self.assertIn("public", self.arch["security"]["zones"])
        self.assertIn("internal", self.arch["security"]["zones"])

    def test_no_fake_agent_api(self) -> None:
        self.assertEqual(self.arch["agent_integration"]["endpoints"], [])
        self.assertEqual(self.arch["agent_integration"]["status"], "BLOCKED_EXTERNAL_NOT_IMPLEMENTED")

    def _mutate_contract(self, relative_path: str, mutation) -> None:
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder)
            shutil.copytree(ROOT / "docs", temp / "docs")
            shutil.copy2(ROOT / "README.md", temp / "README.md")
            path = temp / relative_path
            payload = json.loads(path.read_text(encoding="utf-8"))
            mutation(payload)
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ContractValidationError):
                validate(temp)

    def test_duplicate_trace_id_is_rejected(self) -> None:
        self._mutate_contract("docs/requirements/requirements_contract.json",
                              lambda d: d["traceability"].append(dict(d["traceability"][0])))

    def test_policy_reference_corruption_is_rejected(self) -> None:
        self._mutate_contract("docs/requirements/requirements_contract.json",
                              lambda d: d["requirements"][0].update(security_policy_id="SEC-UNKNOWN"))

    def test_missing_decision_milestone_is_rejected(self) -> None:
        self._mutate_contract("docs/architecture/architecture_contract.json",
                              lambda d: d["open_decisions"][0].update(due_milestone=""))

    def test_fake_approval_without_evidence_is_rejected(self) -> None:
        self._mutate_contract("docs/implementation/phase_01_acceptance.json",
                              lambda d: d["gates"][0].update(status="APPROVED"))

    def test_phase_closed_without_approval_is_rejected(self) -> None:
        self._mutate_contract("docs/implementation/phase_01_acceptance.json",
                              lambda d: d.update(phase_status="CLOSED"))

    def test_invalid_agent_endpoint_is_rejected(self) -> None:
        self._mutate_contract("docs/architecture/architecture_contract.json",
                              lambda d: d["agent_integration"].update(endpoints=["/fake-agent"]))

    def test_pending_phase_marker_is_consistent(self) -> None:
        progress = (ROOT / "docs/implementation/progress.md").read_text(encoding="utf-8")
        self.assertIn("**Marker:** PHASE_01_IMPLEMENTED_AWAITING_VERIFICATION", progress)
        self.assertNotIn("**Marker:** PHASE_01_COMPLETE_READY_FOR_PHASE_02", progress)


if __name__ == "__main__":
    unittest.main()
