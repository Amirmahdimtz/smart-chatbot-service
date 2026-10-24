# Phase 05 — A/B integration plan and evidence policy

**Baseline:** `0c817b1886b1668576e2037394f4b2d5cbf4997b`. This is the planned matrix; actual results are separately recorded in phase_05_evidence.md. Do not infer that unexecuted scenarios have passed. No workstation or On-Prem server test is assumed.

- A: compile/import and DI/web discovery, Ruff, full pytest regression, HTTP 401/403/size/multipart/file negative tests, permissions/identity spoofing, job state/idempotency negative tests, migration metadata, pip-audit strict, SBOM, Docker, gitleaks.
- B: CI service matrix of disposable PostgreSQL 16, S3-compatible object service in loopback namespace, ClamAV socket with updated signatures and dedicated worker process. Use only synthetic generated TXT/PDF and EICAR standard anti-virus test string. Verify upload, quarantined S3 reference, actual clamd verdict, durable job, lease/concurrency/restarts, error path and no automatic publication.
- Failure injection: kill separate worker after commit and during processing; kill/restart S3, ClamAV and PostgreSQL separately; provoke lease expiry and stale ack; reject cross-zone/invalid-credential; force maximum retries and dead letter; include timestamps, job IDs (synthetic), assert DB state, process exit code, and CI URL for each scenario.
- Migration: two upgrades, `--check`, test-only downgrade/upgrade on exclusively disposable *_test database. Do not execute on organizational DBs.
- Evidence acceptance: record exact commit SHA, run ID, command, exit status, test counts, skipped count, service version, failure logs and independent review. A mocked dependency does not satisfy real B.
- C: only deferred verification register entries in Phase18, never requested before Phase18. No technical closure unless A/B critical-path evidence passes.

## CI implementation and mandatory follow-up

Workflow `.github/workflows/phase02-ci.yml` includes a dedicated `ingestion-integration` job with disposable PostgreSQL 16, loopback S3-compatible service and `clamav/clamav:1.4` (preloaded signatures), synthetic-generated per-run object credentials, dedicated subprocess Worker, EICAR test payload and disposable migration reverse/re-upgrade **before test data writes**.

Post-PUT crash/reconciliation, missing S3 object + same-key replay, concurrent claim/lease fencing, dead-letter, cancellation and lease-expiration are now coded and subject to same-head CI acceptance; any CI `skip` is separately counted. Missing multi-process crash DURING malware scan, extended scanner/storage outage and real service restart injection are not to be represented as PASSED until exercised.

## Actual scope after CI 40098047270

Seven actual ingestion integration checks PASS, including real separate Worker OS-kill and lease recovery against PostgreSQL, live ClamAV clean/EICAR, scanner TCP outage/recovery, S3 immutable conditional write/dedup, storage-tamper denial and API negative coverage. Four PostgreSQL regressions and nine Qdrant integration checks PASS. Full container-stop/restart fault injection on S3, ClamAV, and PostgreSQL mid-operation remains REQUIRED A/B and NOT_RUN. Final enterprise HA/DR testing belongs to Group C Phase18.


## Additional real service outage matrix executed

CI run 40098823479 executed tests/test_phase05_service_outages.py in the real Phase05 integration job. Three of three PASS: Docker-paused private S3 refuses reads and returns valid quarantined bytes on resume while durable job remains queued; Docker-paused ClamAV prevents approval and induces durable retry_wait, then real daemon rescan reaches awaiting_approval; Docker-paused PostgreSQL rejects startup, and after resume a fresh DB-backed repository persists/reads a synthetic source. Runner CI, disposable database and unique container names are enforced before pause. The tests unpause each service in finally blocks. They demonstrate service unavailability and recovery, not destruction, cold start or multi-node disaster recovery.
