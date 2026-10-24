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
