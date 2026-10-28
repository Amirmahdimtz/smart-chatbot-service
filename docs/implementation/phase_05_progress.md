# Phase 05 — Durable ingestion-job foundation (partial work, not phase acceptance)

- Baseline: main `0c817b1886b1668576e2037394f4b2d5cbf4997b`, green CI `40092914708`.
- Work authorization: project owner's request to complete the full product; development-only exception ADR-0008.
- Scope implemented in this branch: PostgreSQL versioned ingestion-job schema, scoped idempotent enqueue, SKIP LOCKED worker claims, lease tokens/heartbeat, bounded retries/dead-letter and expired-lease reaping. No HTTP upload or publication is enabled.
- Required before full Phase05 DoD: verified object storage, streaming upload signature/size guards, real malware scan, quarantine, separate runnable Worker, cancellation, real crash/restart recovery including object integrity, security negative cases and synthetic-data end-to-end evidence.
- A tests executed: NONE at authoring time; new tests submitted for GitHub CI. Do not infer PASS.
- B tests executed: NONE at authoring time; real PostgreSQL CI integration added. Evidence must be reviewed before acceptance.
- A/B required but missing: upload/quarantine/AV/object-store/independent Worker integration and scope validation under agreed identity policy; Qdrant unrelated here.
- C tests: `P18-P05-C01`, `P18-P05-C02`, `P18-P05-C03` are DEFERRED_TO_PHASE_18; never PASSED.
- Technical DoD: INCOMPLETE.
- Phase Before: NOT_STARTED; Phase After: IN_PROGRESS, once branch changes are accepted as development work.
- Production Release: NOT_READY. No organization data, deployment, or On-Prem tests.

## Recovery and deployment notes

Apply the versioned Alembic migration only on an approved disposable Postgres integration DB for CI tests. Production schema change requires DBA/change approval and backup. This migration creates a new table; rollback `downgrade -1` removes it and is destructive if jobs have been recorded. The repository's guarded runner only permits test-only downgrade to base on disposable `*_test` databases.

Leases use DB server time; expired attempts can be reclaimed by another worker. Lease token prevents a stale worker from recording successful completion. External side effects MUST be idempotent on immutable job/document-version identity before an actual Worker is introduced. This branch does not implement those external side effects.
