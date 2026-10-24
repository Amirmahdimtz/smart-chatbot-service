# Phase 03 evidence register

**Basis**: live GitHub `main` `eb918b1f27c6028ca9d19c118973d8e165bb661f`, 2026-10-24. Developer reviewed source, GitHub permissions, Phase 01/02 status and ADR-0005.

## Execution state at source drafting

| Category | Test | Status |
|---|---|---|
| A | GitHub main CI / full pytest regression / Ruff / dependency audit | NOT_RUN at drafting; see current Actions before claiming success |
| A | PostgreSQL migration upgrade/re-upgrade/metadata check/isolated integration | NOT_RUN at drafting; dedicated CI `postgres-integration` job added |
| A | Local Python compile/import | NOT_RUN at drafting; GitHub source has not been cloned into the local execution container due to unavailable GitHub DNS |
| B | User Windows PowerShell and Docker PostgreSQL | NOT_RUN — owner transcript required |
| C | On-prem TLS/restore/HA/soak/Public–Internal isolation/approval | NOT_RUN — external test infrastructure and approvals required |

This file is not a PASS claim. After each real execution record source SHA, runner, command, exit code, logs, affected PostgreSQL version, identity/scope (without credentials), and exact Migration revision.

## Verification gates

- Source syntax, imports, DI, existing Phase 01/02 test suite and Ruff; secure dependency audit and CI artifacts.
- Actual PostgreSQL: empty-db upgrade; repeat upgrade; Alembic drift check; synthetic data constraints; scope/owner denied; concurrent sequence; duplicate idempotency; optimistic conflict; FK constraints; rollback.
- Follow-up owner Windows evidence of the same or later SHA and disposable database restore.
- On-prem owner decisions D-07/D-08 and verified physically separate public/internal DB secrets and networking.
- **No `CLOSED` marker without these gates.**
