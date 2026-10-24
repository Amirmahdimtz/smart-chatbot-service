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

## Owner Windows Phase 02 HTTP framing regression verification — 2026-10-24

The project owner supplied a PowerShell transcript from an existing Windows checkout. This transcript itself confirms a clean `main` working tree **and** SHA `5607c51032ff4828822b04fa155add7fc2a38f07` after a successful fast-forward `git pull --ff-only`. The results below are **owner-reported execution evidence** rather than commands run by the technical reviewer.

| Workstation command / check | Actual reported result |
|---|---|
| `git switch main`, `git pull --ff-only` | PASS; repository fast-forwarded to this SHA |
| `git rev-parse HEAD` | `5607c51032ff4828822b04fa155add7fc2a38f07` |
| `git status --short` | Clean (no output) |
| `.venv/Scripts/python.exe -m pip install -r requirements-dev.txt` | PASS; pinned direct requirements already present inside isolated `.venv` |
| `.venv/Scripts/python.exe -m pip check` | PASS: `No broken requirements found.` |
| `.venv/Scripts/python.exe -m pytest -q` | **32 passed, 1 warning in 48.68s**; includes five newly introduced Phase 02 HTTP-framing regression cases |
| `.venv/Scripts/ruff.exe check src tests` | PASS: `All checks passed!` |
| `.venv/Scripts/ruff.exe format --check src tests` | PASS: `17 files already formatted` |
| `.venv/Scripts/pip-audit.exe -r requirements.txt --strict` | PASS: `No known vulnerabilities found` as of this execution |

The non-blocking warning is a `StarletteDeprecationWarning` from the framework TestClient dependency about using `httpx`. It is tracked for dependency-compatibility review; it is not a failing test.

**Precise scope:** This new transcript did **not** rerun the separate compile/Phase 01 contract validator commands, but those checks previously passed in GitHub Actions [run 40072543004](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40072543004) on the same `5607c51032ff4828822b04fa155add7fc2a38f07` source SHA. The same GitHub run had three successful jobs (verify, docker-build, secret-scan), 32 passed tests, Ruff, strict pip-audit and SBOM upload. The earlier Windows HTTP live/startup/ready/unauthenticated metrics smoke check was carried out on a preceding source revision, **not** rerun in this latest Windows transcript.

**Acceptance:** Category B Windows regression, environment and dependency verification for Phase 02 HTTP framing is now evidenced as PASS. Category C remains outstanding: production-equivalent test environments with distinct Public/Internal credentials, real IdP/JWKS rotation, Vault, gateway/TLS/firewall negative tests, authenticated metrics, observability export, HA/restore and responsible-owner approvals. Phase 02 stays `IMPLEMENTED_AWAITING_VERIFICATION`, not `CLOSED`. ADR-0005's conditional development-only Phase 03 gate remains unchanged; Phase 03 remains `NOT_STARTED`.

## Targeted third security review — 2026-10-24

Source baseline: `main` `b478d984b0037adb4432aed516fbba3e17147c0d`. Remediated source SHA: [`ac02b3a42e767bdfc854d01d371713294683d8d3`](https://github.com/Amirmahdimtz/smart-chatbot-service/commit/ac02b3a42e767bdfc854d01d371713294683d8d3).

**Issues fixed and regression evidence:**
1. When 10,000 active client addresses exhausted the local rate-limit tracking table, an unknown client's 429 was previously transmitted **inside** the global async lock. A slow client could prevent unrelated legitimate requests from acquiring that lock. HTTP transmission is now outside the locked state-update region; a concurrent slow-send negative regression test was added.
2. Noncanonical `Content-Length` values (signed, whitespace-padded or comma-delimited) previously passed Python's permissive integer conversion. The middleware now requires an ASCII decimal digit sequence; the negative test rejects invalid representations before the application is invoked.
3. Duplicate `Authorization` headers could be interpreted differently by upstream ingress and app frameworks. Protected routes now reject duplicate credentials with HTTP 400, covered by an actual ASGI/TestClient negative test.

**Actual Category A test evidence:** GitHub Actions [run 40073778225](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40073778225) on `ac02b3a42e767bdfc854d01d371713294683d8d3` ended `SUCCESS` for `verify`, `docker-build` and `secret-scan` (**3/3 PASS**). `pytest -q`: **35 passed, 1 existing Starlette TestClient deprecation warning in 1.69s**. Python compile, both normal and optimized Phase 01 contract validators, Ruff lint and format, strict `pip-audit`, CycloneDX SBOM generation/upload and Docker build executed successfully. These tests cover only synthetic/isolated test traffic; they are not real IdP, Vault, network or Production E2E evidence.

**Category B workstation:** the owner already reported **32/32 PASS** on clean checkout `5607c51032ff4828822b04fa155add7fc2a38f07`. The three new regression tests introduced at `ac02b3a42e767bdfc854d01d371713294683d8d3` have **NOT** been reported as run on Windows. Do not attribute the earlier workstation transcript to the new revision.

**Phase 02 formal status:** `IMPLEMENTED_AWAITING_VERIFICATION` throughout this review. Production-equivalent separate Public/Internal credentials, real JWKS/SSO and rotation, Vault, TLS/ingress, actual isolation and forbidden cross-zone probes, authorized metrics, on-prem tracing, load/HA/DR and Security/Operations owner approval remain open. Conditional Phase 03 development-only decision in ADR-0005 remains effective; no Phase 03 implementation has started.

## Windows security audit network timeout after 35-test remediation — 2026-10-24

The project owner submitted a new PowerShell transcript with the following **owner-reported Category B evidence** from a clean `main` checkout at commit `6348cd89b693c48367fa44ecf63ea0068e3f6222` (SHA printed in the same transcript after `git pull --ff-only` and clean `git status --short`):

| Check | Observed owner result |
|---|---|
| `git switch main`, `git pull --ff-only`, `git rev-parse HEAD` | PASS; source SHA `6348cd89b693c48367fa44ecf63ea0068e3f6222` |
| `git status --short` | PASS, no local changes |
| `.venv/Scripts/python.exe -m pytest -q` | **35 passed, 1 warning in 40.33s** (one existing `StarletteDeprecationWarning` in framework TestClient) |
| `.venv/Scripts/ruff.exe check src tests` | **PASS**, `All checks passed!` |
| `.venv/Scripts/ruff.exe format --check src tests` | **PASS**, `17 files already formatted` |
| `.venv/Scripts/pip-audit.exe -r requirements.txt --strict` | **INCONCLUSIVE — NETWORK READ TIMEOUT**, not a detected vulnerability and not a PASS; `requests.exceptions.ReadTimeout` accessing `pypi.org:443`, socket read timeout 15 seconds |

**Independent Category A evidence:** the exact same commit `6348cd89b693c48367fa44ecf63ea0068e3f6222` had previously passed GitHub Actions [run 40073950447](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40073950447): 3/3 jobs succeeded, 35 pytest passed, Ruff and `pip-audit -r requirements.txt --strict` passed, SBOM artifact uploaded and Docker image built. That CI scan is actual evidence of an advisory lookup at CI execution time; it does **not** convert the timed-out Windows scan into a local PASS.

**Non-destructive remediation instruction:** once network connectivity permits, rerun `./.venv/Scripts/pip-audit.exe -r requirements.txt --strict --timeout 60` (Windows use `.\\.venv\\Scripts\\pip-audit.exe`). The `--timeout` socket option is documented upstream. Preserve the exact output and exit code. If it still times out, test outbound HTTPS access to `pypi.org` and review DNS/proxy/firewall settings without disabling TLS verification. No package upgrade, security exception, or fake offline audit is warranted based only on this timeout.

**Acceptance and gate:** local 35-test regression is PASS; local vulnerability lookup is **NOT_VERIFIED_DUE_TO_NETWORK**; CI vulnerability audit is PASS as of its run. Phase 02 stays `IMPLEMENTED_AWAITING_VERIFICATION`, real on-prem security/IdP/Vault/network owner tests and sign-offs remain outstanding, and the previously documented conditional development-only technical gate for Phase 03 remains unchanged. No Phase 03 implementation started.

## Independent Phase 02 acceptance re-audit: JWKS lifespan restart — 2026-10-24

**Repository baseline:** `main` `62e47279a935c798a2d2b9606d3c8f9ecb161e13`; code fix commit [`7c620b0018ce209197ff4df560fa1d076508ac47`](https://github.com/Amirmahdimtz/smart-chatbot-service/commit/7c620b0018ce209197ff4df560fa1d076508ac47).

**Scope:** Re-evaluated the implementation plan's Phase 02 DoD against actual FastAPI startup/shutdown, DI, JWT validation/JWKS refresh, Vault boundary, per-process request security, telemetry, public/internal deployment manifests, Docker/CI, and Phase 01/02 markers. The earlier production-equivalent IdP/Vault/two-zone, gateway, ingress security and sign-off gaps are not resolved by source inspection or unit tests.

**Root cause corrected:** The FastAPI lifespan previously closed `TokenValidator`'s `httpx.AsyncClient` on shutdown without explicitly resetting cached signing keys/refresh attempt state. A later startup of the same app instance could believe old keys were still fresh, skip fetching JWKS under the retry cooldown, and start the refresh task with a **closed HTTP client**. The delayed background refresh could then crash or fail to renew keys; this is a lifecycle correctness/readiness risk.

**Implementation:** `TokenValidator.open_async()` recreates an HTTP client only if the existing client is closed and is invoked before each FastAPI startup JWKS fetch. `close_async()` cancels the periodic refresh task, closes its client and clears cached verification keys, wall-clock cache time and cooldown state. This forces a fresh trusted JWKS lookup on re-startup. MockTransport is used **only in the regression test**.

**New regression:** `test_validator_reinitializes_jwks_client_and_cache_across_app_lifespans` exercises two successive TestClient lifespans for a single FastAPI instance, verifies that each start fetches JWKS and returns readiness 200, and that each shutdown closes the client and makes validator readiness false.

**Category A actual CI evidence:** [GitHub Actions run 40075776482](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40075776482), source `7c620b0018ce209197ff4df560fa1d076508ac47`, finished `SUCCESS`; `verify`, `docker-build` and `secret-scan`: **3/3 PASS**. Pytest **36 passed, 1 known framework warning in 1.50s**; compile, normal and optimized Phase 01 validators (both PASS), Ruff lint/format PASS, strict pip-audit `No known vulnerabilities found` at execution, and SBOM/gitleaks artifacts generated/uploaded.

**Category B:** The latest owner Windows transcript remains **35 passed** on the earlier source SHA `6348cd89b693c48367fa44ecf63ea0068e3f6222` and reported a `pypi.org` network read timeout during a local audit. The newest 36th regression has **not yet been run by the owner on Windows**; no local PASS claim is made for it. The previous failed local advisory lookup has not been resolved by this code change.

**Category C / Owner gates:** Real org IdP/JWKS rotation (including second lifespan), Vault trust/auth/secret lifecycle, two genuinely separate test deployments and credentials, ingress/TLS and firewall deny probes, authorized metrics, tracing exporter, distributed quotas, load/HA/recovery and approved security sign-off remain **NOT_RUN / AWAITING_APPROVAL / BLOCKED_DECISION** according to their respective evidence needs.

**Disposition:** Phase 02 status remains `IMPLEMENTED_AWAITING_VERIFICATION` (no closure marker); Phase 01 status unchanged. ADR-0005's `TECHNICAL_GO_FOR_DEVELOPMENT_ONLY` remains a **conditional authorization** for isolated Phase 03 work after explicit owner instruction, **not** Phase 02 `CLOSED` or Production permission.
