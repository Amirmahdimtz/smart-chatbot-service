# Phase09 — A/B test matrix (start only)

| ID | Group | Requirement | Test or action | Current status |
| --- | --- | --- | --- | --- |
| P09-A01 | A | Prompt template v1, deterministic real ID/span/canonical checksum | `tests/test_phase09_answering.py::test_prompt_is_deterministic_and_source_offsets_are_real` | PENDING_CI |
| P09-A02 | A | Untrusted document role injection remains data, no tool permission | `tests/test_phase09_answering.py::test_untrusted_document_cannot_become_system_role` | PENDING_CI |
| P09-A03 | A | No evidence → abstain without model invocation | `tests/test_phase09_answering.py::test_no_evidence_abstains_without_model_call` | PENDING_CI |
| P09-A04 | A | Fake citation, duplicate JSON key, invalid schema and model output rejection | `tests/test_phase09_answering.py::test_exhaustive_fake_citation_and_structured_response_rejection` | PENDING_CI |
| P09-A05 | A | Citation budget, invalid domain/role and span, duplicate source | `tests/test_phase09_answering.py` negative tests | PENDING_CI |
| P09-B01 | B | Real approved self-hosted LLM serving, deterministic metadata, license/provenance | D-02, actual model/endpoint and test corpus | REQUIRED_NOT_RUN |
| P09-B02 | B | Real Persian answer grounding and Citation Precision/Faithfulness Gold Set | Approved domain Gold Dataset and model | REQUIRED_NOT_RUN |
| P09-B03 | B | Real server streaming, timeout, cancellation, concurrency and model outage | Actually running isolated self-hosted model | REQUIRED_NOT_RUN |
| P09-B04 | B | Mid-query authorization/revoke, stale span and evidence validity after generation | Complete Phase07/08 actual authorization/publish E2E | REQUIRED_NOT_RUN |
| P09-B05 | B | Injection, outdated/conflicting sources, ungrounded claims and abstention rates | Genuine model/provider and scored dataset | REQUIRED_NOT_RUN |
| P09-B06 | B | Structured model response parser invalid modes and safety evaluation | Genuine LLM response corpus | REQUIRED_NOT_RUN |

All Group C `P18-P09-C01..C06` are deferred to Phase18; unrun tests must never be labeled PASS. The matrix is not an acceptance record.
