# Phase 02 execution evidence (2026-10-21)

- Baseline `main`: `c5e40aaaca4316620ddeba2b5c260396e3c9263f` (connector GET ref/tree).
- GitHub repo: `Amirmahdimtz/smart-chatbot-service`, public, authenticated push/admin confirmed.
- Prior Phase 01: `IMPLEMENTED_AWAITING_VERIFICATION` and all formal acceptance gates still pending; continuation explicitly authorized for **development only** per ADR-0004.
- Source scope: Phase 02 runtime/DI/config/authz/HTTP security/telemetry, operational docs, Docker, CI and tests. No database, migration, Qdrant, real Agent or model added.

## Category A — isolated execution

Local isolated Phase 02 source tree (not cloned from live GitHub due container DNS resolution error):

- `python -m compileall -q src tests`: PASS (local authored source).
- `python -m pytest -q tests/test_phase02_runtime.py`: PASS 10/10 after correcting a mistaken negative-test expectation (`403`, not `401`, for a correctly authenticated user without permission).
- `python -c 'from src.host.app import create_app; app=create_app(); ...'`: PASS; five injectable providers and four deterministic health/metrics routes.

These facts are **not** claims about CI or about a persisted `main` checkout. Final SHA verification, GitHub runner results, full Phase 01 regression, Ruff formatting, pip-audit, Docker build and SBOM must be recorded separately once run. Full on-prem SSO/Vault/network/monitoring/load/HA checks: `NOT_RUN`.

## Status and blockers

Implementation is at most `IMPLEMENTED_AWAITING_VERIFICATION` after verified GitHub commit and current-source regression. Until that verification, report only the evidence above. D-01, D-05, D-07, D-08, D-15, D-16 and D-18 remain under decision; final acceptance requires Security/IAM/Infrastructure owners and operational tests. Forward-only Git revert is the recovery path.

## GitHub CI verification and remediation (real runner evidence)

- Initial Phase 02 CI run [39601249439](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/39601249439): Docker build and secret scan PASS; Python compile, Phase 01 validator and tests PASS; verify job FAILED on Ruff lint. Source corrected through CI-generated formatting patch. Temporary diagnostic workflow was removed in a forward-only commit.
- Follow-up CI run [39602337454](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/39602337454): Ruff lint PASS, format check FAILED on a nested helper in tests; corrected in subsequent commit.
- Security audit run [39602466213](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/39602466213): Python checks and Ruff PASS; `pip-audit --strict` FAILED with reported advisories for PyJWT 2.13.0 and transitive Starlette 0.50.0. Requirements upgraded to PyJWT 2.15.1, FastAPI 0.156.8, Starlette 1.9.0 and OpenTelemetry API 1.45.1. No advisories were suppressed.
- First upgraded Framework test run [39602682366](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/39602682366): 21 of 22 tests passed; one test assumed the old FastAPI internal `app.routes` representation. The test was changed to assert operational HTTP routing, not framework internals.
- **Successful main-run evidence:** [39602864124](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/39602864124), commit `b84ee4205cb8bd29cd66555173577d51bb0162fc`: `verify`, `docker-build` and `secret-scan` all **PASS**. Python tests **22/22 PASS**; Phase 01 validators normal and `-O` PASS; Ruff Lint/Format PASS; pip-audit strict PASS; CycloneDX SBOM generation and artifact upload PASS.
- **Final code-source verification:** [39603186801](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/39603186801), commit `a8315728b84ff64892a92c169c14acb5c08bc5c4`: full workflow **SUCCESS**, all jobs (`verify`, `docker-build`, `secret-scan`) PASS. `python -m pytest -q`: **23 passed, 1 framework deprecation warning**. Compile, Phase 01 validators, Ruff check/format, `pip-audit --strict`, SBOM generation/upload and secret-scan also PASS. `dependency-sbom` and `gitleaks-results.sarif` verified in workflow artifacts.
- Baseline-to-code-source compare: 35 paths affected (31 added, four modified, none deleted), seven forward-only commits; prior Phase 01 contracts, approvals, migrations and production data not modified. One prior Phase 01 test file was formatting-only adjusted to satisfy repository-wide lint.
- This evidence-document-only follow-up commit does not change runtime, configuration, dependencies or tests; its own workflow result must be checked separately before claiming that final documentation SHA passed CI.
- GitHub Actions evidence is actual CI, not a completed organizational IdP/Vault/network or production release test. Formal Phase 01 approvals remain pending.

## Owner-reported Windows workstation run — 2026-10-21

**Source:** project owner supplied an actual Windows PowerShell transcript from a checkout of `main` at `916a0031eb43b5806ffbb29cfc859a12fe246f2e`. Evidence in this section is **owner-reported**, not commands run by this assistant.

| Verification | Observed result |
|---|---|
| `git clone`, `switch main`, `pull --ff-only` | Success; checkout HEAD exactly matches source SHA above; working tree clean |
| `py -3.12 -m venv .venv` | Success creating the environment |
| `Activate.ps1` | **BLOCKED** by Windows PowerShell Execution Policy (`PSSecurityException`) |
| `python -m pip install -r requirements-dev.txt` | Install command succeeded, but transcript resolved installed packages under system-wide Python; `.venv` was **not activated**, so isolation was not verified |
| `python -m compileall -q src scripts tests` | PASS |
| `python scripts/validate_phase01.py` and `python -O scripts/validate_phase01.py` | PASS; 8 gates, 19 linked Markdown files, 20 decisions, 9 policies, 21 requirements and 7 scenarios |
| `python -m pytest -q` | **23/23 PASS** in 51.09s; one non-blocking `StarletteDeprecationWarning` for `httpx` |
| `ruff check src tests`, `ruff format --check src tests` | PASS, 15 files reported already formatted |
| `pip-audit -r requirements.txt --strict` | PASS: no known vulnerabilities returned at time of audit |
| `python -m uvicorn ... --port 5000` | Startup completed but **binding FAILED** with Windows `WinError 10048` (local port occupied); graceful shutdown followed |
| Windows live/startup/ready/metrics HTTP responses | **NOT_RUN / NO_EVIDENCE** because the server failed to bind |

**Root-cause disposition:** both observed blockers are local environment/process conflicts, not reproduced application defects. No production code change is justified by this transcript. Follow the updated [Phase 02 Windows runbook](../operations/phase02_runbook.md): invoke `.venv\\Scripts\\python.exe` directly and run Uvicorn on an available port, then capture observed HTTP responses. Never terminate an unknown PID or change machine-wide PowerShell policy.

**Remaining Category B evidence:** successful `.venv`-isolated install/tests and live loopback HTTP response probes. **Category C** (real IAM/SSO, Vault, firewall isolation, distributed limits, load, HA/restore) remains NOT_RUN; approvals remain outstanding. Phase 02 stays `IMPLEMENTED_AWAITING_VERIFICATION`; Phase 01 G-01–G-08 remain unchanged.

## Follow-up owner-reported Windows isolation verification — 2026-10-21

The owner supplied a subsequent PowerShell transcript from the same local repository working directory. No new checkout SHA was shown in this transcript; the earlier confirmed **runtime source checkout** was `916a0031eb43b5806ffbb29cfc859a12fe246f2e`. Do not infer that the newer docs-only commit was already pulled.

| Verification | Observed result |
|---|---|
| `.\\.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt` | **PASS**, installed pinned dev requirements in the virtual environment |
| Virtual interpreter identity (`sys.executable`) | **PASS**, path terminates in the repository's `.venv\\Scripts\\python.exe` |
| `.\\.venv\\Scripts\\python.exe -m pip check` | **PASS**, `No broken requirements found.` |
| `.\\.venv\\Scripts\\python.exe -m pytest -q` | **23/23 PASS** in **28.43 s**, with one known non-blocking Starlette test-client deprecation warning |
| Local port 5000 listener inspection | Confirmed `127.0.0.1:5000` occupied by a Windows process; no kill/restart performed |
| `Get-Process -Id <7356>` | PowerShell **ParserError** because the literal angle brackets were pasted; this is a shell syntax error, not an application failure |
| Alternate-port Uvicorn startup and live/startup/ready/metrics HTTP status checks | **NOT_RUN / NO_EVIDENCE** |

**Resolution:** virtual-environment isolation and regression test evidence are now verified from owner logs (Category B). The PowerShell PID inspection syntax is `Get-Process -Id 7356` for that historical PID, or use the updated runbook's dynamic PID lookup; literal angle brackets must not be included. For runtime HTTP smoke tests, use an available loopback port and report the four actual HTTP codes. No runtime code changes, database changes, Qdrant operations or production credentials were required.

**Outstanding:** Category B real loopback HTTP smoke test, Category C IdP/SSO/Vault/network/isolation/operational evidence, and formal approvals. Phase 02 remains `IMPLEMENTED_AWAITING_VERIFICATION`; Phase 01 acceptance gates are not altered. No personal filesystem path or OS account identifier has been retained in this note.

## Owner-reported Windows HTTP smoke verification — 2026-10-21

The owner provided an additional PowerShell transcript from the previously tested local checkout. The **exact checkout SHA at this HTTP run was not reprinted**, so only the earlier confirmed source SHA (`916a0031eb43b5806ffbb29cfc859a12fe246f2e`) is known. This is **owner-provided execution evidence**, not an HTTP request or Windows command executed by this assistant.

- `Get-Process -Id 7356`: the existing port-5000 listener was identified as `com.docker.backend` (Docker Desktop). The process was inspected, not stopped.
- `Get-NetTCPConnection -LocalPort 5051 -State Listen`: no listener was reported before starting this service.
- With `SCB_ENV=development`, `SCB_ZONE=public`, and `.venv` Python, Uvicorn reported successful application startup and `Uvicorn running on http://127.0.0.1:5051`.
- A separate PowerShell terminal queried `http://127.0.0.1:5051/api/v1/health_check`. Actual observed HTTP statuses:

| Endpoint | Observed HTTP code | Expected development code | Result |
|---|---:|---:|---|
| `/live` | 200 | 200 | **PASS** — liveness |
| `/startup` | 200 | 200 | **PASS** — startup |
| `/ready` | 503 | 503 | **PASS** — expected **not ready** without configured IdP (not production readiness) |
| `/metrics`, unauthenticated | 401 | 401 | **PASS** — unauthenticated access denied; authorized retrieval not verified |

Windows PowerShell displayed its legacy `Invoke-WebRequest` content-parsing security prompt for successful responses; the operator acknowledged it for each response. This was a **PowerShell client warning**, not a server error. The runbook now uses `-UseBasicParsing` to suppress the legacy client prompt.

**Disposition:** the previously pending **Category B virtual-environment plus local HTTP smoke test is now evidenced as PASS**, limited to the documented development configuration and unauthenticated metrics request. No organizational IAM/SSO, Vault, dual-deployment Public/Internal isolation, TLS, authorized metrics read or operational HA/DR behavior was verified by this run. Runtime, dependency, and test-source files were **not modified** for this evidence update.

**Open gate:** Phase 02 remains `IMPLEMENTED_AWAITING_VERIFICATION`; Phase 01 approvals are unchanged. This latest transcript did **not** include a fresh `git rev-parse HEAD`; matching an exact commit should be reconfirmed before formal acceptance.
