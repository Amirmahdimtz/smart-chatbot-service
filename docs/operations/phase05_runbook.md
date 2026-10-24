# Phase 05 operations and recovery runbook — synthetic integration only

Status: development-only under ADR-0008; no organizational or production infrastructure actions authorized. Current source is the open Phase05 draft PR #3, not main.

## Startup preconditions

- Python dependencies pinned in `requirements.txt`, separate real isolated PostgreSQL 16 disposable database ending `_test`; schema at `0002_ingestion`; one S3-compatible quarantine bucket with **public ACL disabled**; genuine ClamAV `clamd` with preloaded/up-to-date signatures. No real data or credentials.
- Explicit `SCB_ENV=development`, `SCB_ZONE=internal`, `SCB_DATABASE_ENABLED=true`, `SCB_INGESTION_ENABLED=true`. Environment-sourced `SCB_DATABASE_URL`, `SCB_INGESTION_S3_URL=http://127.0.0.1:9000`, S3 access/secret keys and `SCB_INGESTION_CLAMD_HOST=127.0.0.1` are test-only. Do not commit or echo key values. A bearer token comes from an isolated synthetic IdP with permission `knowledge:test:ingest` and subject `synthetic-*`.
- Run migration separately, never in FastAPI startup: `python src/infrastructure/scripts/run_migrations.py --upgrade` and `--check` on disposable test DB. Reverse only `--downgrade-test-only` on a purposely disposable and emptied DB; the downgrade discards Phase05 jobs/audit and is **destructive**.
- Start API using existing documented host process; start `python -m src.host.ingestion_worker` as a **separate process**, not FastAPI BackgroundTasks. Only test CI defines container setup; no default production enablement exists.

## Health, operation, incident response

- A request writes a durable `staging` intent before S3 PUT, then queues only after storage integrity HEAD. Worker acquires PostgreSQL `SKIP LOCKED` lease, periodically heartbeats and reads quarantined bytes bounded by config. A clean literal ClamAV verdict yields `completed/awaiting_approval`; malware yields `dead/malware_detected`; timeouts/outages yield bounded retry or dead letter. No publication, indexing or external download route exists.
- Inspect only ID, scope, event and **redacted error_code**, never document bytes/object-key/secret in logs. `GET /api/v1/knowledge/jobs/{uuid}` and `GET /api/v1/knowledge/versions/{uuid}` require verified synthetic owner identity; foreign principal returns not-found/forbidden.
- Restart after crash: existing leased jobs are reclaimed after expiry; stale final attempts move to dead; committed staged PUTs older than 30s are reconciled using SHA-256, never silently published. For missing S3 objects older than 300s: `dead/staging_abandoned` and same-key safe retry are supported. While S3 is down, staged intents remain unapproved. An operator must reconcile any long-lived failed staging before cleanup.
- Stop new requests, send SIGTERM to worker, allow bounded in-flight work to complete; interrupted leased job is recoverable after lease expires. Shut API before storage/DB if safe. Rollback of code without destructive schema change is preferred; require approval and verified disposable backup before any irreversible DB rollback.
- When scanner is unavailable or signatures stale, disallow upload approval and investigate daemon health/version. Scanner is not bypassed. Before any real deployment, apply organization Security + Data Governance policies and Phase18 approval. **Never request organization On-Prem tests in Phase05**.

## A/B verification

- `python -m compileall -q src scripts tests`, `pytest -q`, `ruff check src tests`, `ruff format --check src tests`; current CI owns security scan, SBOM and Docker image build.
- `pytest -q tests/test_phase05_integration.py` only when the synthetic-only environment is explicitly enabled, real PostgreSQL, storage and scanner are running, and all test data/credentials are disposable. A successful unit/protocol mock test does not replace this.
- Record exact SHA/runner/service versions, count of PASS/FAIL/SKIP, security findings and links in `phase_05_evidence.md`. Do not claim production readiness. Organization restore, HA/DR, IDP/Vault, security UAT and load/soak are deferred to Phase18 register C01–C08.

## Open operational constraints

D-07/D-08 policy, real retention/purge, object-store vendor trust, organization network and rate capacity are unapproved. No HR/PII import, organization publishing or production public upload.
