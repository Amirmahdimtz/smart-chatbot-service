# Phase 05 — Evidence and verification register (development only)

Baseline main SHA: `0c817b1886b1668576e2037394f4b2d5cbf4997b`. Branch: `feat/phase05-ingestion`; PR [#3](https://github.com/Amirmahdimtz/smart-chatbot-service/pull/3), Draft. Tests have synthetic data only; no server organization access requested.

## Historical A/B successful source-specific run

[GitHub CI 40095593728](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40095593728), head `d769ff7c19b441e25ad678d3c7b45548cfbbdbb4` (before staging crash-recovery amendments):

- **A:** `verify` success: compile, both architecture validators, `pytest -q` **69 passed, 10 skipped, 1 warning**; Ruff check/format PASS; strict pip-audit **No known vulnerabilities found**; SBOM generated.
- **B:** `ingestion-integration` success: **3 passed**, real ephemeral PostgreSQL + versioned Migration up/repeat/check/disposable reverse/up, S3-compatible object integrity, ClamAV clean/EICAR actual scanner and separate independent Worker OS process. This is NOT evidence for amended recovery code on later SHA.
- **Regression:** `postgres-integration` success; `qdrant-integration` success; `docker-build` success; `secret-scan` success. Six jobs total success.
- **Historical failure remediation:** run 40094557202 failed Ruff Format; run 40095000375 failed worker completion because `document_version.state` VARCHAR(16) could not fit `awaiting_approval`; migration and model were widened and CI 40095593728 passed.
- **Later B-only success:** [CI 40095766199](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40095766199) succeeded in ingestion/postgresql/qdrant/secret scan/docker jobs (with newer recovery tests), but full run failed Ruff import-order check. This is not whole-run success.

## Required A/B not yet accepted

Final same-SHA full CI after recovery improvements; nontrivial failure-injection (scanner/storage service outage/timeouts, crash during scan), static review of worker shutdown/retry/lease semantics and malformed multipart/security cases, source image supply-chain approval, independent Technical Acceptance. No skipped integration check may be called PASS without its matching isolated CI B run.

## Group C not executed

`P18-P05-C01`–`P18-P05-C08` each `DEFERRED_TO_PHASE_18`. No final organization IdP/Vault, public/internal network enforcement, load, Soak, HA/DR, object-storage enterprise restore/retention or UAT evidence exists. D-07/D-08 are not approved.

**Technical DoD Status:** PENDING. **Phase Status:** IN_PROGRESS / cannot close until final evidence and independent review. **Production Release Status:** NOT_READY.

## Extended source-matched Group A/B evidence, 2026-10-24

- Source commit: bf6137dc64761ba2120c79128d630c12ed8e9b49; CI: https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40098047270 . All six jobs passed on this commit, before this documentation-only revision.
- Tests A Executed + Actual Results: general pytest 74 passed, 14 skipped, one third-party deprecation warning; Python compile and Phase01 validators PASS; Ruff check and format PASS; strict pip-audit found no known vulnerabilities; SBOM generated; Docker build and secret scan PASS.
- Tests B Executed + Actual Results: isolated real S3-compatible/ClamAV/PostgreSQL integration 7 passed, one warning; independent Worker OS kill and lease reclaim, scanner TCP outage/recovery, real EICAR rejection, idempotency and conditional S3 writes, tamper rejection, pagination/authorization and multipart negatives. PostgreSQL regression 4 passed; Qdrant regression 9 passed (six warnings). Disposable Alembic repeated upgrade, drift check and test-only reverse/upgrade PASS. No organization On-Prem service used.
- Tests A/B Required but Missing: real container stop/restart injection for S3, ClamAV and PostgreSQL while in-flight jobs are active; reviewed integrity/provenance and immutable digest for the community CI S3 image; accountable independent security/architecture verification and final sign-off. They are NOT_RUN, not waived or passed.
- Tests C Deferred to Phase 18: organization data policy/identity, physical isolation, storage backup/restore, enterprise scanner and rotation, HA/DR, capacity/load/soak and final security/UAT. All remain DEFERRED_TO_PHASE_18, not passed.
- Phase 18 Verification Register IDs: P18-P05-C01, P18-P05-C02, P18-P05-C03, P18-P05-C04, P18-P05-C05, P18-P05-C06, P18-P05-C07, P18-P05-C08.
- Technical DoD Status: PENDING remaining A/B and independent technical acceptance. Phase Status Before/After: IN_PROGRESS -> IN_PROGRESS (original NOT_STARTED -> IN_PROGRESS is recorded). Production Release Status: NOT_READY. D-07/D-08 remain BLOCKED_DECISION for real data; Phase15 Agent remains BLOCKED_EXTERNAL.

General test skips are not reclassified as passes. Real integration evidence comes separately from the named B jobs. Historical failed CI runs remain failures; this later successful source-matched result supersedes only their outstanding technical regressions.


## Final synthetic-service verification update — digest-pinned revision

- Tested source: 6fc7e39f39e2f5bd9ca8399ae7a03c809ae48ac0. GitHub CI https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40098823479 : ALL SIX JOBS SUCCESS.
- Tests A Executed + Actual Results: general 74 passed / 17 skipped / one third-party test-client warning; Python compile and architecture validators PASS; Ruff lint/format PASS; strict pip-audit no known vulnerabilities; SBOM, Docker build and secret scan SUCCESS.
- Tests B Executed + Actual Results: 7 real ingestion integration tests PASS; 3 real Docker pause/unpause dependency fault-injection tests PASS (PostgreSQL, ClamAV and S3-compatible storage); 4 PostgreSQL regression and 9 Qdrant regression tests PASS. Independent Worker OS kill and lease reclaim, scanner outage and real recovery, EICAR, immutable S3 conditional writes, changed-object rejection, concurrent claims, expired lease/dead letter and negative API cases covered. CI S3 and ClamAV images pinned to the exact registry digests observed in the prior successful runner. No organization On-Prem tests executed.
- Tests A/B Required but Missing: independently verified supply-chain provenance/signature and security assessment of community S3 test image; separate stop/recreate crash scenario rather than pause/unpause for each dependency, if required by technical reviewer. Operational signature/update monitoring and approval for any real deployment remain outside this synthetic-only scope. The accountable independent Technical Verifier has not approved the implementation.
- Tests C Deferred to Phase 18: all eight On-Prem controls P18-P05-C01 through P18-P05-C08 remain DEFERRED_TO_PHASE_18; no PASSED claim and no requirement to execute them during Phase05.
- Phase 18 Verification Register IDs: P18-P05-C01, P18-P05-C02, P18-P05-C03, P18-P05-C04, P18-P05-C05, P18-P05-C06, P18-P05-C07, P18-P05-C08.
- Technical DoD Status: PENDING (provenance, independent review and any reviewer-required crash/recreate negative scenario). Phase Status Before/After: IN_PROGRESS -> IN_PROGRESS. Production Release Status: NOT_READY. D-07/D-08 real-data decisions unapproved; Agent is BLOCKED_EXTERNAL.
- Source-matched evidence is deliberately separate from this documentation-only follow-up commit. Run acceptance checks on the final documentation SHA before asserting identical-SHA acceptance. The earlier historical failures remain recorded and were not retroactively changed to PASS.
