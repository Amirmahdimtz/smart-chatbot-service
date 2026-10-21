"""Phase 01 contract regression tests: no runtime or optional dependencies."""
import json
import unittest

from scripts.validate_phase01 import (
    ARCHITECTURE, REQUIREMENTS, REQUIRED_CASES, validate
)


class Phase01ContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.req = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
        cls.arch = json.loads(ARCHITECTURE.read_text(encoding="utf-8"))

    def test_contract_validation_and_links(self):
        result = validate()
        self.assertEqual(result["scenarios"], 7)
        self.assertEqual(result["requirements"], 21)

    def test_every_domain_is_mapped(self):
        self.assertEqual({s["id"] for s in self.req["scenarios"]}, REQUIRED_CASES)
        self.assertEqual(len(self.req["traceability"]), len(self.req["requirements"]))

    def test_security_and_isolation_not_omitted(self):
        self.assertFalse(self.arch["platform"]["pgvector_permitted"])
        self.assertIn("public", self.arch["security"]["zones"])
        self.assertIn("internal", self.arch["security"]["zones"])
        self.assertIn("SEC-02", self.arch["security"]["policy_ids"])

    def test_no_agent_api_or_active_route_is_fabricated(self):
        self.assertEqual(self.arch["agent_integration"]["endpoints"], [])
        self.assertEqual(self.arch["agent_integration"]["status"],
                         "BLOCKED_EXTERNAL_NOT_IMPLEMENTED")
        self.assertTrue(all(p["status"] == "CANDIDATE_NOT_IMPLEMENTED"
                            for p in self.arch["api_boundaries"]))

    def test_no_deferred_decision_claimed_closed(self):
        self.assertTrue(all(d["status"] == "OPEN" for d in self.arch["open_decisions"]))
        self.assertTrue(all(not d["owner_confirmed"] for d in self.arch["open_decisions"]))


if __name__ == "__main__":
    unittest.main()

