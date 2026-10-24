# Phase 05 — A/B integration plan and evidence policy

**Baseline:** `0c817b1886b1668576e2037394f4b2d5cbf4997b`. All results below **NOT_RUN** until direct CI evidence is collected. No workstation or On-Prem server test is assumed.

- A: compile/import and DI/web discovery, Ruff, full pytest regression, HTTP 401/403/size/multipart/file negative tests, permissions/identity spoofing, job state/idempotency negative tests, migration metadata, pip-audit strict, SBOM, Docker, gitleaks.
- B: CI service matrix of disposable PostgreSQL 16, S3-compatible object service in loopback namespace, ClamAV socket with updated signatures and dedicated worker process. Use only synthetic generated TXT/PDF and EICAR standard anti-virus test string. Verify upload, quarantined S3 reference, actual clamd verdict, durable job, lease/concurrency/restarts, error path and no automatic publication.
- Failure injection: kill separate worker after commit and during processing; kill/restart S3, ClamAV and PostgreSQL separately; provoke lease expiry and stale ack; reject cross-zone/invalid-credential; force maximum retries and dead letter; include timestamps, job IDs (synthetic), assert DB state, process exit code, and CI URL for each scenario.
- Migration: two upgrades, `--check`, test-only downgrade/upgrade on exclusively disposable *_test database. Do not execute on organizational DBs.
- Evidence acceptance: record exact commit SHA, run ID, command, exit status, test counts, skipped count, service version, failure logs and independent review. A mocked dependency does not satisfy real B.
- C: only deferred verification register entries in Phase18, never requested before Phase18. No technical closure unless A/B critical-path evidence passes.

## CI implementation and mandatory follow-up

Workflow `.github/workflows/phase02-ci.yml` includes a dedicated `ingestion-integration` job with disposable PostgreSQL 16, loopback S3-compatible service and `clamav/clamav:1.4` (preloaded signatures), synthetic-generated per-run object credentials, dedicated subprocess Worker, EICAR test payload and disposable migration reverse/re-upgrade **before test data writes**.

Post-PUT crash/reconciliation, missing S3 object + same-key replay, concurrent claim/lease fencing, dead-letter, cancellation and lease-expiration are now coded and subject to same-head CI acceptance; any CI `skip` is separately counted. Missing multi-process crash DURING malware scan, extended scanner/storage outage and real service restart injection are not to be represented as PASSED until exercised.
