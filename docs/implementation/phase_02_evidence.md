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
