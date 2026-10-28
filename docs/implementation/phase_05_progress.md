# Phase 05 — Durable ingestion-job foundation (partial work, not phase acceptance)

- Baseline: main `0c817b1886b1668576e2037394f4b2d5cbf4997b`, green CI `40092914708`.
- Work authorization: project owner's request to complete the full product; development-only exception ADR-0008.
- Scope implemented in this branch: PostgreSQL versioned ingestion-job schema, scoped idempotent enqueue, SKIP LOCKED worker claims, lease tokens/heartbeat, bounded retries/dead-letter and expired-lease reaping. No HTTP upload or publication is enabled.
- Required before full Phase05 DoD: verified object storage, streaming upload signature/size guards, real malware scan, quarantine, separate runnable Worker, cancellation, real crash/restart recovery including object integrity, security negative cases and synthetic-data end-to-end evidence.
- Tests A Executed + Actual Results: [PR CI 40677892309](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40677892309) on code SHA `86034adcdd3c256871c565445b4e6620e10fbca2`: verify SUCCESS — `45 passed / 8 skipped` in general Pytest; Python compile, phase01 validators (normal/optimized), Ruff lint/format, strict pip-audit (`No known vulnerabilities found`), SBOM, Docker build, gitleaks all PASS. Eight skips are service-only tests; not counted as PASS in the general job.
- Tests B Executed + Actual Results: same-source CI PostgreSQL 16 isolated synthetic `5 passed` (Phase03 and Phase05; includes leased worker concurrency, stale token fence, retry exhaustion and idempotency), repeated migration upgrade, schema drift check, test-only downgrade/upgrade PASS. Qdrant disposable regression `9 passed` (Phase04 regression only, not Phase05 storage/scanner proof). No organizational service was tested.
- A/B required but missing: upload/quarantine/AV/object-store/independent Worker integration and scope validation under agreed identity policy; Qdrant unrelated here.
- C tests: `P18-P05-C01`, `P18-P05-C02`, `P18-P05-C03` are DEFERRED_TO_PHASE_18; never PASSED.
- Technical DoD: INCOMPLETE.
- Phase Status Before/After: `NOT_STARTED` → `IN_PROGRESS` on this development branch (not a CLOSED marker; `main` remains unchanged until review/merge).
- Production Release: NOT_READY. No organization data, deployment, or On-Prem tests.

## Recovery and deployment notes

Apply the versioned Alembic migration only on an approved disposable Postgres integration DB for CI tests. Production schema change requires DBA/change approval and backup. This migration creates a new table; rollback `downgrade -1` removes it and is destructive if jobs have been recorded. The repository's guarded runner only permits test-only downgrade to base on disposable `*_test` databases.

Leases use DB server time; expired attempts can be reclaimed by another worker. Lease token prevents a stale worker from recording successful completion. External side effects MUST be idempotent on immutable job/document-version identity before an actual Worker is introduced. This branch does not implement those external side effects.

## CI source evidence

- [GitHub Actions 40677892309](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40677892309): 5/5 SUCCESS (verify, PostgreSQL, Qdrant, Docker, secret scan). This verifies the partial durable-job feature, not the Phase05 full DoD.
- Earlier PR CI failures (DI-count test, unused import and Ruff formatting) were corrected; they remain visible in GitHub Actions history. No unexecuted check is recorded as PASS.
