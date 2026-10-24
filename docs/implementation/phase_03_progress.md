# Phase 03 progress

- Phase: `PHASE_03` — PostgreSQL Operational Schema & Migration.
- Before: `NOT_STARTED`; development entry: `ADR-0005` conditional technical permission.
- Current: `IN_PROGRESS` while CI, local and security/infrastructure verification are pending.
- Baseline: `main` `eb918b1f27c6028ca9d19c118973d8e165bb661f`.
- Implemented source planned: SQLAlchemy async DB context, six scoped structural models, generic BaseRepository, conversation repository/service, Alembic initial revision and guarded migration runner, isolated PostgreSQL tests and runbook.
- Phase 01/02 remain `IMPLEMENTED_AWAITING_VERIFICATION`; no other phase automatically starts.
- Blockers: D-07/D-08 IAM/classification/retention/approval; isolated organizational PostgreSQL/TLS/Public–Internal isolation; no live organization test evidence.
- Marker: **not issued** until committed code and test results establish the appropriate state.
- Related: [ERD and decisions](phase_03_design.md), [evidence](phase_03_evidence.md), [runbook](../operations/phase03_runbook.md).
