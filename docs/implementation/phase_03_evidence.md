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

## Verified GitHub execution — 2026-10-24

- Baseline: `eb918b1f27c6028ca9d19c118973d8e165bb661f`. Initial Phase 03 code: `114ece53594f340e5543c17a6eed49c97d455524`; Ruff import-order failure in that run was corrected by `462411bfbb921cb52f6a2b0361631aee4c1a730d`.
- Successful source: [commit `462411bfbb921cb52f6a2b0361631aee4c1a730d`](https://github.com/Amirmahdimtz/smart-chatbot-service/commit/462411bfbb921cb52f6a2b0361631aee4c1a730d); [Actions run 40078990354](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40078990354). All **four** jobs `verify`, `postgres-integration`, `docker-build`, `secret-scan`: **SUCCESS**.
- `verify`: `python -m compileall -q src scripts tests` PASS; Phase 01 validators normal and `-O` both PASS; `pytest -q` **38 passed, 1 skipped, 1 known Starlette warning**. The skip is specifically the integration test without a PostgreSQL URL in the general verification job; it runs in the dedicated PostgreSQL job. `ruff check src tests` PASS; `ruff format --check src tests` PASS; `pip-audit -r requirements.txt --strict` **No known vulnerabilities found**; CycloneDX SBOM generation/upload PASS.
- `postgres-integration`: GitHub Actions isolated PostgreSQL **16.15**, synthetic `scb_phase03_test` database; first Alembic `--upgrade` PASS; repeated `--upgrade` PASS; `--check` reports **No new upgrade operations detected**; `pytest -q tests/test_phase03_postgresql.py`: **3 passed** (metadata/negative config/real PostgreSQL constraints and concurrent transactional operations); `--downgrade-test-only`, re-upgrade and repeat drift check PASS. This is a destructive reverse strategy **only on ephemeral CI test database**, not a proof of production backup/restore.
- PostgreSQL expected negative-test ERROR entries for forbidden composite FK scope, duplicate message sequence, duplicate version, and RESTRICT delete appear in PostgreSQL service log; those errors are intentional inputs under `pytest.raises(IntegrityError)` and do not represent failing integration tests.
- `docker-build`: PASS. `secret-scan`: PASS. No credentials for organization systems, no real HR/PII records, and no shared PostgreSQL touched.
- Documentation-only status commit `ae46126266d8b55857077480f7c0792e174fad9a`: [CI 40079253726](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40079253726) 4/4 jobs PASS.

## Still pending

- **B — Windows:** owner must run `git pull --ff-only`, dependency installation, complete regression, real isolated Docker PostgreSQL, metadata check and safe local reverse test. No Windows execution has been provided for Phase 03.
- **C — On-Prem:** separate Public/Internal PostgreSQL network, role/credential isolation, organization CA/TLS, migrations and verified backup/PITR restore, deadlocks/soak/load/HA, D-07/D-08 classification/retention/consent/approval and Security/Infrastructure/Privacy sign-offs. **NOT_RUN**.
- **Benchmark:** no throughput, database latency, QPS, RPO or RTO values measured or claimed.
- Outcome: `IMPLEMENTED_AWAITING_VERIFICATION`; marker `PHASE_03_IMPLEMENTED_AWAITING_VERIFICATION` is justified for source and CI but not `CLOSED`.

## Latest source validation — scope gate and CRUD transaction coverage

- [Commit `35bbff3ec9d5b806904b8c0be5427e8c92fd3fd7`](https://github.com/Amirmahdimtz/smart-chatbot-service/commit/35bbff3ec9d5b806904b8c0be5427e8c92fd3fd7) adds `ConfigReader` constructor injection to `ConversationService` and validates that every requested `scope` equals deployment configuration; adds negative cross-zone tests, generic repository CRUD / caller-owned rollback integration and production empty-password configuration denial.
- [CI run 40079517611](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40079517611): **4/4 jobs PASS**, same-day GitHub Actions. `verify`: compile PASS; both Phase 01 validators PASS; **38 pytest passed, 1 PostgreSQL-only test skipped, 1 known Starlette warning**; Ruff lint PASS (`All checks passed!`); Ruff format PASS (`26 files already formatted`); `pip-audit --strict` PASS (`No known vulnerabilities found`); SBOM generation/upload PASS.
- `postgres-integration` with isolated PostgreSQL 16.15: migration upgrade/re-upgrade PASS; Alembic `--check`: `No new upgrade operations detected`; real `tests/test_phase03_postgresql.py` **3 passed in 0.93s**; disposable test-only downgrade/re-upgrade and final `--check` PASS. Three pytest tests contain multiple assertions for concurrency, owner/cross-zone isolation, scoped FKs, unique constraints, transaction rollback and generic repository CRUD. No separate per-assertion pass counts claimed.
- `docker-build` PASS; `secret-scan` PASS.
- No real organization data or organization database touched. At the time of this CI execution, Windows verification had not yet been submitted; later owner-reported results are documented below. Organizational backup/restore, TLS/network isolation and policy approval remain outstanding.

## Owner-reported Windows workstation verification — 2026-10-24

**Provenance:** Project owner supplied the PowerShell transcript for a clean Windows checkout. These commands were executed by the owner, **not** by this assistant. No connection URL, password, workstation user path, personal data or test database contents are committed.

- Repository: `main`, local `HEAD=61ad27287b34693314466d2727d9e676f1d0cb08`, `git pull --ff-only` fast-forward succeeded and `git status --short` had no output. The tested checkout includes the final Phase 03 runbook change.
- Python 3.12 virtual environment and pinned requirements installed successfully; `pip check`: `No broken requirements found`; `compileall -q src scripts tests`: exited without reported error.
- `scripts/validate_phase01.py` both normal and `python -O`: `PHASE_01_CONTRACT_VALIDATION_OK` (8 acceptance gates, 21 requirements, 7 scenarios).
- Initial `python -m pytest -q`: **38 passed, 1 skipped, 1 known StarletteDeprecationWarning in 74.08 s**. The skip is the real PostgreSQL integration test when no isolated DB URL is configured; that test is executed separately below.
- `ruff check src tests`: `All checks passed!`; `ruff format --check src tests`: `26 files already formatted`.
- `pip-audit -r requirements.txt --strict --timeout 60`: **INCONCLUSIVE / NETWORK_ERROR**, aborted with `requests.exceptions.ConnectionError` wrapping `RemoteDisconnected('Remote end closed connection without response')`. No audit completion or vulnerability finding was reported. **Do not count as local security PASS.** GitHub CI on the same source dependencies previously passed strict `pip-audit`; local network connectivity remains to be rechecked.
- Isolated `postgres:16` Docker container (`scb_phase03_test` using synthetic credentials/data): immediate first `pg_isready` returned `no response`. This is consistent with startup timing, **not proof of a durable failure**: subsequent connection and Alembic operations completed successfully. Exact Windows-side PostgreSQL minor version and initial readiness delay were not captured.
- `run_migrations.py --upgrade` twice: no errors in transcript; `--current`: **`0001_foundation (head)`**; `--check`: **`No new upgrade operations detected.`**
- `pytest -q tests/test_phase03_postgresql.py`: **3 passed in 15.38 s**, exercising actual isolated PostgreSQL. The second general regression, after clearing PostgreSQL-specific environment variables: **38 passed, 1 skipped, 1 known framework warning in 47.33 s**.
- No Windows `--downgrade-test-only` was run. Reverse/re-upgrade was verified **only in ephemeral GitHub CI**, not on the workstation. No Windows backup/restore drill was evidenced.
- Follow-ups: review local outbound HTTPS/PyPI connectivity and rerun strict vulnerability audit; capture a fresh successful `pg_isready` before migrations on future test-container starts (bounded readiness loop added to the runbook); keep credentials out of logs.
- Phase 03 **remains `IMPLEMENTED_AWAITING_VERIFICATION`**: organization PostgreSQL with independent Public/Internal credentials, TLS/roles, backup/PITR restore, load/HA/DR, policy D-07/D-08 and sign-offs are **NOT_RUN / AWAITING_APPROVAL**. No `PHASE_03_CLOSED` marker.
