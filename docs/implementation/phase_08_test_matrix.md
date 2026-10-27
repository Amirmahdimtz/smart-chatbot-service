# Phase08 — A/B Matrix, first development slice (NOT phase closure)

| ID | Group | Requirement | Test | Status at creation |
| --- | --- | --- | --- | --- |
| P08-A01 | A | Reuse Persian query normalizer and invalid-input rejection | `tests/test_phase08_retrieval.py` query tests | PENDING_CI |
| P08-A02 | A | RRF determinism, duplicate/provenance reject, configurable rank constant | `tests/test_phase08_retrieval.py` fusion tests | PENDING_CI |
| P08-A03 | A | Fail-closed Qdrant payload, denied zones, foreign docs, spoofed published flag | `tests/test_phase08_retrieval.py` service tests | PENDING_CI |
| P08-B01 | B | Actual authenticated Qdrant filter on synthetic published fixture and deny-all authoritative gate | `tests/test_phase08_qdrant.py` isolated CI | PENDING_CI |
| P08-B02 | B | Actual PostgreSQL source/version/owner/domain revocation and denied prepublication | `tests/test_phase08_postgres.py` disposable CI | PENDING_CI |
| P08-B03 | B | Real approved query encoder and real dense retrieval measured against Gold Set | D-03, Phase07 publication | REQUIRED_NOT_RUN |
| P08-B04 | B | Genuine sparse/lexical candidate provider and fusion comparison | D-04 | REQUIRED_NOT_RUN |
| P08-B05 | B | Genuine versioned Reranker provider/lifecycle + timeout, score sanity | D-03 | REQUIRED_NOT_RUN |
| P08-B06 | B | Fully approved published index, mid-query revoke, source revision, consistency/race | Real PG/Qdrant + Phase07 cutover | REQUIRED_NOT_RUN |
| P08-B07 | B | Mixed Persian, contradicted/outdated, zero evidence, abstention, context budgets | Authorized Gold Dataset | REQUIRED_NOT_RUN |
| P08-B08 | B | Dense-only vs sparse-only vs hybrid vs rerank Recall/nDCG/MRR and p95 | Gold Dataset and D-12 | REQUIRED_NOT_RUN |

Group C `P18-P08-C01..C06` deferred exclusively to Phase18, never counted PASS. This matrix is a plan; outcomes reside in `phase_08_evidence.md`.

| P08-A04 | A | Whole-excerpt evidence budget, no-source abstention hints, checksum/conflict rejection | `tests/test_phase08_evidence_budget.py` | PENDING_SAME_SHA_CI |
