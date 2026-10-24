# Phase 03 PostgreSQL — isolated development operations

## Safety boundary

Use only a personally owned, disposable PostgreSQL database ending in `_test` and synthetic data. **Do not run any of these migrations on shared/organization/production PostgreSQL**. PostgreSQL is authoritative; no Qdrant resources are provisioned. Database opt-in is `SCB_DATABASE_ENABLED=true`; default is disabled to avoid changing Phase 02 runtime until configured.

Connection configuration is validated by `ConfigReader` and injected into `PsqlDbContext`. Provide **exactly one** of `SCB_DATABASE_URL` or `SCB_DATABASE_VAULT_PATH`, not both. Vault uses existing `SCB_VAULT_ENABLED`, `SCB_VAULT_TOKEN`, `SCB_VAULT_ADDRESS`, and KV v2 secret field `url`. URL scheme is `postgresql+asyncpg`. For integration/staging/production set `SCB_DATABASE_TLS_MODE=verify-full`, optionally `SCB_DATABASE_TLS_CA_FILE` to a trusted CA path. The default local-development mode disables TLS; never copy it to production.

Pool defaults: size=5, overflow=5, pool wait=10s, connect=5s, statement=30000ms; validated in `DatabaseSettings`. SQLAlchemy parameters are hidden from SQL logs. Runtime creates one engine/sessionmaker per app lifespan; each repository transaction receives a separate session and commits/rolls back atomically. Readiness fails if enabled database cannot connect or revision differs from `0001_foundation`.

**Least privilege:** use distinct application and migration PostgreSQL roles, separate Public/Internal databases and credentials, restricted network ingress, SSL verification and external secret management. The current schema does not configure organization roles, network isolation, RLS, retention or HR access; each requires infrastructure/security sign-off before live-data use.

## Windows PowerShell — owner-executed checks

From repository root on Windows with Python 3.12 and Docker Desktop:

```powershell
git switch main
git pull --ff-only
git rev-parse HEAD
git status --short
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src scripts tests
.\.venv\Scripts\python.exe scripts/validate_phase01.py
.\.venv\Scripts\python.exe -O scripts/validate_phase01.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
.\.venv\Scripts\pip-audit.exe -r requirements.txt --strict --timeout 60
```

For the isolated PostgreSQL test (requires Docker; never run against a real dataset):

```powershell
$testPassword = [guid]::NewGuid().ToString("N")
docker run -d --name scb-phase03-postgres -p 127.0.0.1:55433:5432 -e POSTGRES_USER=scb_test -e POSTGRES_PASSWORD=$testPassword -e POSTGRES_DB=scb_phase03_test postgres:16
docker exec scb-phase03-postgres pg_isready -U scb_test -d scb_phase03_test
$env:SCB_ENV = "development"
$env:SCB_ZONE = "public"
$env:SCB_DATABASE_ENABLED = "true"
$env:SCB_DATABASE_URL = "postgresql+asyncpg://scb_test:${testPassword}@127.0.0.1:55433/scb_phase03_test"
$env:SCB_PHASE03_TEST_DATABASE_URL = $env:SCB_DATABASE_URL
.\.venv\Scripts\python.exe src/infrastructure/scripts/run_migrations.py --upgrade
.\.venv\Scripts\python.exe src/infrastructure/scripts/run_migrations.py --upgrade
.\.venv\Scripts\python.exe src/infrastructure/scripts/run_migrations.py --current
.\.venv\Scripts\python.exe src/infrastructure/scripts/run_migrations.py --check
.\.venv\Scripts\python.exe -m pytest -q tests/test_phase03_postgresql.py
# Clear the PostgreSQL test URL before running deployment-independent regressions.
Remove-Item Env:SCB_PHASE03_TEST_DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:SCB_DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:SCB_DATABASE_ENABLED -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest -q
```

`--downgrade-test-only` **drops all six foundation tables**; run only after explicitly confirming the test database is disposable, has no needed data and its name ends `_test`. To test reverse/reinstall in that scenario:

```powershell
.\.venv\Scripts\python.exe src/infrastructure/scripts/run_migrations.py --downgrade-test-only
.\.venv\Scripts\python.exe src/infrastructure/scripts/run_migrations.py --upgrade
.\.venv\Scripts\python.exe src/infrastructure/scripts/run_migrations.py --check
```

After collecting evidence, stop/remove the disposable test container only when its data is no longer needed. Remove or clear session environment variables containing credentials. Do not paste passwords or full database URLs into shared logs.

Expected: all full regression tests PASS; test suite including PostgreSQL assertions passes when the test URL is present; `--current` prints `0001_foundation`; repeat upgrade and `--check` return exit code 0; invalid config raises redacted `ConfigurationError`. If PostgreSQL is absent, integration tests SKIP — report **NOT_RUN**, not PASS. Send commit SHA, anonymized command output, exit codes, PostgreSQL version and Docker readiness logs, with secrets redacted.

## Organization staging, backup and recovery (NOT_RUN)

Before any approved schema change: assign signed change owner, freeze versioned migration and verified backup/PITR restore point, record PostgreSQL/driver/SQLAlchemy/Alembic versions, verify TLS/role grants, and schedule a separate public/internal sandbox run. PostgreSQL migration role requires DDL; runtime role should not. Apply upgrade once; `--current` and `--check` compare. If failure occurs, stop writes and triage current revision; **do not run destructive downgrade on a shared DB**. Restore a verified backup or use separately approved forward-only corrective migration. Perform and time a restore integrity drill, RPO/RTO and failover evidence before any production release. Test concurrent migration attempts, lock contention, long transactions, deadlocks, pool saturation and backpressure. Independent security/IAM/Privacy/Operations owner sign-offs are outstanding.
