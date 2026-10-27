# Phase06 remediation: bounded chunk count, honest source-span audit

Date: 2026-10-27
Status: DEVELOPMENT_FIX — INDEPENDENT_REVIEW_REQUIRED
Parent: `feat/phase06-persian-processing` (Draft PR #4). This fix is staged in a separate Draft PR; no merging or prior phase closure is authorized.

## Correction to the previous audit finding

The previous claim that `group_start` and `group_end` persisted across extracted pages was **incorrect**. In the original source they are initialized **inside** `for page in pages`. Thus there was no demonstrated inter-page state leakage in Phase06. A real multi-page regression test is added to document correct page-relative offsets. The extra assignments to `group_start=None` and `group_end=0` added in Phase07's dependent branch are redundant; do not treat those assignments as proof of a fixed defect, and remove/reconcile them during branch integration.

## Actually verified code defect

In the original `IngestionRepository.finish_async`, when `success=True` but the candidate batch is missing or contains more than 4096 chunks, the method returns `False` without changing the `leased` job/version state. `IngestionWorkerService.run_once_async` ignores this boolean result and returns `True`. The lease may therefore expire and be diagnosed as `lease_expired`, obscuring the actual bounded-input failure; no document evidence is saved.

## Remediation contract

- `chunk_pages` fails with nonretriable `ProcessingRejected("too_many_chunks")` before creating the 4097th chunk. Its output remains deterministic for 4096 chunks or fewer, and source mappings are unchanged.
- `finish_async` remains defensive against invalid caller batches: an empty batch yields `empty_chunk_batch`, and a batch longer than 4096 yields `too_many_chunks`, regardless of worker version. Under a currently valid fenced PostgreSQL lease it atomically changes the job to `dead`, the DocumentVersion to `failed`, clears the lease, and commits an audit event with the true reason. The source is not published and no partial chunks are stored. Expired or stolen leases retain the original `False` fencing semantics.
- Group A tests cover exact 4096 and 4097 count, multi-page deterministic source spans; CI Group B exercises genuine isolated PostgreSQL terminal transitions, audit and zero persisted chunks for invalid batches.

## Explicit boundaries and status

This work does **not** select a real Embedding model (D-03), satisfy Phase07 publication or lift Phase05/06 specialist review requirements. No organization On-Prem Group C tests are requested: `P18-P06-C01..C06` remain `DEFERRED_TO_PHASE_18` and **NOT_RUN**. Review and CI outcomes must be recorded by exact tested source SHA.

Phase06 Technical DoD: **PENDING_REVIEW**; Phase06 existing state remains `IMPLEMENTED_AWAITING_VERIFICATION` or as separately documented by the authoritative Phase06 record (not automatically changed by this fix).
Production release status: **NOT_READY**.


## Executed A/B evidence and closure decision — 2026-10-27

**Exact code source SHA:** `ea832ca7f57bf6a7a5f4d92c431f4a716ce3f5f0`
**Completed Actions run:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40522144231 — **6/6 SUCCESS**: verify, postgres-integration, qdrant-integration, ingestion-integration, docker-build, secret-scan.

**Tests A Executed + Actual Results:** General Python suite `95 PASSED / 30 SKIPPED / 2 warnings`, including tests for exact 4096 acceptable chunk count, 4097 nonretriable rejection and three-page exact raw offsets; Ruff Check/Format PASS, compile/import and strict pip-audit PASS (no known vulnerabilities), SBOM/Docker/secret-scan jobs SUCCESS. SKIP is not PASS.

**Tests B Executed + Actual Results:** Real isolated PostgreSQL `tests/test_phase06_chunk_limit_integration.py` **2 PASSED** (empty/oversized batch terminal `dead` with actual error_code and audit, version `failed`, zero KnowledgeChunk rows, stale finalization denied). Other isolated CI regression: Phase05 S3/ClamAV/PostgreSQL ingestion **13 PASSED**; actual Persian and Arabic scanned PDF OCR **2 PASSED** (CER=0.000 on these tiny synthetic fixtures only); actual fault injection/recovery **8 PASSED**; standalone PG **4 PASSED**; Qdrant **9 PASSED**. These integration tests exercise actual disposable test services, not corporate servers.

**Initial failed attempts, never reported as PASS:** [40521198658](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40521198658) failed due to incorrect test boundary fixture (multi-codepoint string) and overly long test Worker ID; [40521869104](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40521869104) had valid Python test execution but `verify` failed an outstanding Ruff formatting difference. Final source-matched 40522144231 passed all six.

**Tests A/B Required but Missing:** Separate Phase06 expert evaluation of complex Persian/Arabic mixed/OCR/table/religious quotations and attributable independent Backend/Architecture + Security acceptance of current Phase06 dependency; predecessor Phase05 independent review/risk ADR-0008 remains unsigned. These remain Phase06 closure gates; this focused patch only remediates chunk bound behavior, not all Phase06 quality obligations.

**Tests C Deferred to Phase18:** `P18-P06-C01` through `P18-P06-C06` all `DEFERRED_TO_PHASE_18` / NOT_RUN / NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P06-C01, C02, C03, C04, C05, C06.
**Technical DoD Status:** `BOUNDARY_FIX_A_B_VERIFIED — PHASE06_FULL_DOD_PENDING_REVIEW`.
**Phase Status Before/After:** `IMPLEMENTED_AWAITING_VERIFICATION → IMPLEMENTED_AWAITING_VERIFICATION` (no automatic change to prior accepted record).
**Production Release Status:** `NOT_READY`.

This evidence appendix is a documentation-only commit after the source-matched CI SHA; any CI run on the later documentation-only head must be considered separately. Draft PR only, not merged; all dependent stacked Phase07–09 branches need an explicit reviewed reconciliation/backport when merging is authorized.
