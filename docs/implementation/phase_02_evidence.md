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

## Phase 02 targeted security remediation (2026-10-24)

Baseline main source SHA: `2f52c58c2be1f15831b2226c7c4591eb809e08b9`. Runtime changes are restricted to JWKS cache lifecycle/refresh throttling, ASGI timeout correctness, and expired rate-limit cache eviction. Dedicated negative/concurrency/TTL regression tests are added to `tests/test_phase02_security_regressions.py`. On-prem IdP, Vault, gateway isolation, HA, trace exporter and supply-chain digest decisions remain untested/unapproved. Phase 02 is still `IMPLEMENTED_AWAITING_VERIFICATION`; Phase 01 approval state is unchanged.

CI results must be recorded only after real execution. Local runtime cannot clone GitHub due DNS/network restrictions; therefore full-project local tests have not been claimed here.

## Verified source remediation CI — 2026-10-24

- Source commit: [56efee12f1e8b67493e946e5d6936915528df66f](https://github.com/Amirmahdimtz/smart-chatbot-service/commit/56efee12f1e8b67493e946e5d6936915528df66f), branch main.
- GitHub Actions [run 40070131736](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40070131736): **SUCCESS**; verify, docker-build and secret-scan each **SUCCESS**.
- Verify job executed Python compile, both normal and optimized Phase 01 contract validators (**PASS**), pytest (**27 passed, 1 known framework deprecation warning**), Ruff check and format (**PASS**), pip-audit requirements strict (**no known vulnerabilities found at execution time**), SBOM generation/upload (**PASS**).
- Four new regression tests in the file named tests/test_phase02_security_regressions.py cover expired rate-limit bucket eviction, timeout-before/after-headers, concurrent unknown JWT key IDs and periodic JWKS refresh, and stale-key failure on IdP outage. These are actual CI tests with MockTransport solely in test fixtures, not organizational IdP/Proxy E2E verification.
- Earlier CI runs failed exclusively on introduced Ruff lint/format issues; two forward-only follow-up commits corrected those issues. A temporary diagnostic workflow was removed from the final source tree.
- Live IdP/Vault, authorized metrics retrieval, independent public/internal network and credential boundary, distributed edge rate limits, image digest/lockfile policy, tracing export, HA and DR remain **NOT_RUN / BLOCKED_DECISION or BLOCKED_EXTERNAL** as applicable. No Phase 02 CLOSED marker is issued.

## Owner-reported Windows verification after Phase 02 remediation — 2026-10-24

The project owner supplied a 103-line Windows PowerShell transcript after previously demonstrating a clean local `main` checkout at commit `c95c8bbe1c9982d5f9c806837350afc52c9c87bf` (the earlier `git pull --ff-only` and `git rev-parse HEAD` were shown in a separate message). The new testing transcript itself does **not** print a fresh `git rev-parse HEAD`. It is therefore **owner-reported local execution, contextually attributable** to the previously confirmed checkout, not an independently captured SHA within the test output.

| Category B check | Actual observed result |
|---|---|
| `.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt` | All requirements already satisfied inside the repository's isolated `.venv` |
| `.venv\\Scripts\\python.exe -m pip check` | `No broken requirements found.` |
| `.venv\\Scripts\\python.exe -m compileall -q src scripts tests` | Completed without reported errors |
| `.venv\\Scripts\\python.exe scripts/validate_phase01.py` | `PHASE_01_CONTRACT_VALIDATION_OK`: 8 gates, 19 linked Markdown files, 20 open decisions, 9 policies, 21 requirements, 7 scenarios |
| `.venv\\Scripts\\python.exe -O scripts/validate_phase01.py` | Same `PHASE_01_CONTRACT_VALIDATION_OK` result |
| `.venv\\Scripts\\python.exe -m pytest -q` | **27 passed, 1 warning in 60.51 seconds**; all four added Phase 02 security-regression tests included in the suite |
| `.venv\\Scripts\\ruff.exe check src tests` | `All checks passed!` |
| `.venv\\Scripts\\ruff.exe format --check src tests` | `16 files already formatted` |
| `.venv\\Scripts\\pip-audit.exe -r requirements.txt --strict` | `No known vulnerabilities found` at execution time |

**Warning:** `StarletteDeprecationWarning` emitted from the installed FastAPI/Starlette TestClient dependency for using `httpx`; the warning is non-blocking but remains a framework-upgrade compatibility item.

**Evidence classification:** This transcript verifies Windows Category B isolated setup, source compilation, Phase 01 contract validation, full 27-test regression, lint/format and strict runtime requirements audit. The independently confirmed GitHub Actions [run 40070252396](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40070252396) for source/document commit `c95c8bbe1c9982d5f9c806837350afc52c9c87bf` completed **SUCCESS** in all three jobs. No file changes, CI rerun, or on-prem service interactions occurred as part of the owner's PowerShell transcript.

**Still open:** Real IdP/JWKS key-rotation and outage behavior, Vault HTTPS and secret lifecycle, authorized metrics retrieval, dual-zone credential/network isolation, trusted proxy and distributed limits, external monitoring/tracing, base-image/lockfile policy, load/HA/DR and owner acceptance. These remain Category C `NOT_RUN` or approval/decision dependent. Phase 02 remains `IMPLEMENTED_AWAITING_VERIFICATION` and no `CLOSED` marker is justified. Do not treat a clean dependency audit as proof that deployment and runtime security are complete.

## Phase 02 independent technical re-audit and HTTP framing remediation — 2026-10-24

**Repository baseline:** `main` `2b4ffaae6ba0730d3c0296be5116bcbf26816796`. Independent review checked current `src/host`, authentication, JWKS cache, DI, request guard, configuration, Docker, CI, security threat model and the implementation-plan Phase 02 DoD.

**New root causes, now fixed:**
1. The pre-handler body-size gate previously buffered only POST/PUT/PATCH/DELETE, allowing GET/HEAD/OPTIONS payloads to bypass the actual-body cap if Content-Length was absent or understated. It now validates the actual bytes of every HTTP method.
2. Recording every request frame in an event list had unbounded per-frame overhead for arbitrarily many tiny or empty frames; bounded byte aggregation and one normalized replay frame now limit payload memory to the configured byte budget (subject to ordinary per-request Python overhead).
3. Duplicate Content-Length, simultaneous Content-Length and Transfer-Encoding, and declared-versus-observed body length ambiguity now fail closed with HTTP 400 before the downstream app runs.

**Tests added:** `tests/test_phase02_http_edge_cases.py` contains five actual ASGI regression cases for oversized chunked GET, repeated empty-frame aggregation, mismatched length, ambiguous framing, and legitimate multipart-frame replay. Existing JWT/DI/health tests continue as regressions.

**Execution evidence:** [GitHub Actions run 40072315115](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40072315115) for source SHA `f01862d66e67c547df1638cc80fdd931bac1b3da` finished **SUCCESS**: verify, docker-build and secret-scan **3/3 PASS**; **32 pytest PASS, 1 known Starlette deprecation warning in 1.65 s**; both Phase 01 validators, Ruff lint/format, strict pip-audit, SBOM generation and upload **PASS**. Earlier source CI for SHA `c8632bad4bdad24274ff56687fe06a8c94949793` had 32 pytest PASS but a **Ruff formatting-only failure**, resolved by follow-up SHA `f01862d66e67c547df1638cc80fdd931bac1b3da`. This is actual GitHub CI, not a claim of current Windows/On-Prem tests for the new five cases.

**Acceptance classification:** source-level Phase 02 security/HTTP foundations have CI evidence. Actual two-zone credentials, real IdP/SSO and JWKS rotation, Vault, TLS and ingress controls, real Public/Internal network isolation, authorized metrics, on-prem telemetry, HA/restore and Security/Infrastructure Owner approvals remain **UNVERIFIED / BLOCKED_EXTERNAL or BLOCKED_DECISION**. `IMPLEMENTED_AWAITING_VERIFICATION` is retained; `CLOSED` is not granted. See [ADR-0005](../decisions/ADR-0005-phase03-conditional-development-gate.md) for the separate **conditional development-only** Phase 03 technical gate.
