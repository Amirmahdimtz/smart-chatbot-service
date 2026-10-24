# Phase 02 — Runtime, security and operations runbook

## Status and prerequisite

This release provides HTTP runtime foundation and authentication/authorization enforcement only. It does **not** provide chat, database, Qdrant, AI models or Agent functions. Phase 01 has not been formally accepted. Default `development` deliberately has no IdP: `/live` and `/startup` return 200 but `/ready` returns 503 until valid JWKS configuration exists. Do **not** treat health-only startup as an application ready for production.

## Local Windows PowerShell

The supported local Python version is 3.12. Run the commands from the repository root (the directory containing `requirements-dev.txt`). For an **existing clone**, use `git switch main` and `git pull --ff-only`; **do not clone again inside it**. For a fresh clone only, run `git clone https://github.com/Amirmahdimtz/smart-chatbot-service.git` from the intended parent directory, then `cd smart-chatbot-service`.

PowerShell script execution policy may prevent running `Activate.ps1`. **Activation is optional:** using the interpreter and tools within `.venv\Scripts` directly avoids changing execution policy, avoids installing packages globally, and makes the test environment reproducible. Never change machine-wide execution policy merely for the project.

```powershell
git switch main
git pull --ff-only
git rev-parse HEAD
git status --short
py -3.12 -m venv .venv

.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests scripts
.\.venv\Scripts\python.exe scripts/validate_phase01.py
.\.venv\Scripts\python.exe -O scripts/validate_phase01.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
.\.venv\Scripts\pip-audit.exe -r requirements.txt --strict
```

Confirm that `sys.executable` resolves inside `.venv\Scripts`, not the system-wide Python installation. The expected Phase 02 test baseline is **23 passing tests**; a framework deprecation warning about `starlette.testclient`/`httpx` is presently non-blocking and must be tracked, not misreported as a failed test.

Before binding an HTTP port, inspect it instead of killing an unknown process:

```powershell
Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

If port 5000 is occupied, use another **verified available** local port; port `5051` is an example, not a guaranteed free port. In the first terminal:

```powershell
$env:SCB_ENV = "development"
$env:SCB_ZONE = "public"
.\.venv\Scripts\python.exe -m uvicorn src.host.app:app --host 127.0.0.1 --port 5051 --no-access-log
```

Do not consider the process running until Uvicorn reports `Uvicorn running on http://127.0.0.1:5051`. A subsequent `WinError 10048` means the process failed to bind; pick an available port and retry without changing application code.

In a second PowerShell terminal:

```powershell
$base = "http://127.0.0.1:5051/api/v1/health_check"
foreach ($endpoint in @("live", "startup", "ready", "metrics")) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing "$base/$endpoint"
        "$endpoint : $([int]$response.StatusCode)"
    }
    catch {
        if ($null -ne $_.Exception.Response) {
            "$endpoint : $([int]$_.Exception.Response.StatusCode)"
        }
        else {
            throw
        }
    }
}
```

Expected without an approved IdP: **live=200, startup=200, ready=503, metrics=401**. Windows PowerShell 5.1 may prompt about HTML parsing if `-UseBasicParsing` is omitted; this option avoids that client-side prompt for the local checks. If the test identity provider is explicitly approved/configured with HTTPS JWKS and correct issuer/audience, readiness may become 200. The service is **not production-ready** merely because liveness and startup succeed. Stop the Uvicorn process with Ctrl+C.

To inspect a bound port **without copying placeholders containing angle brackets**, run:

```powershell
$listener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
$listener | Select-Object LocalAddress, LocalPort, OwningProcess
$listener | ForEach-Object { Get-Process -Id $_.OwningProcess }
```

Alternatively, if the current observed PID is `7356`, the syntax is `Get-Process -Id 7356` (**not** `Get-Process -Id <7356>`). PIDs may change between checks. Do not terminate a process until its owner/purpose is confirmed. Keep logs sanitized: share the Git SHA, exit codes, test summary and observed HTTP statuses, not local account names, full filesystem paths, tokens or IdP addresses.

## Docker / two-zone configuration

```powershell
Copy-Item deploy/public.env.example deploy/public.env
Copy-Item deploy/internal.env.example deploy/internal.env
# Replace .invalid examples with the approved real endpoints (do not commit env files).
docker compose -f deploy/compose.yaml config
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml up -d
docker compose -f deploy/compose.yaml ps
docker compose -f deploy/compose.yaml logs --tail 50
docker compose -f deploy/compose.yaml down
```

Both instances listen on host loopback only and have distinct Compose bridge networks. These are testable *process isolation* defaults, not proof of firewall/organization network segregation. Reverse proxy/gateway must enforce TLS (approved certificates), explicit network ACLs, distributed request limits, trusted proxy headers, upstream timeouts and audit retention. No host DB/HR/Agent connectivity must be granted to `public-api`. The deployment examples must be populated and reviewed before execution, and `docker compose up` should fail if JWKS cannot be loaded at startup. Container runs as UID 10001 with read-only filesystem. Never use public `.invalid` examples as operational configuration.

## Authentication / Vault / Observability

`SCB_JWKS_URL`, `SCB_ISSUER` and `SCB_AUDIENCE` are required outside development; `SCB_ZONE` must explicitly be `public` or `internal`; `SCB_CORS_ORIGINS` is a JSON list of approved HTTPS origins. Only RS256 bearer tokens with verified `iss/aud/exp/iat/nbf/sub` are accepted. `roles` and `permissions` must be signed lists of bounded strings; **any** caller-supplied identity/role header is rejected. Identity claims and role mappings must be validated with the real IAM owner; the reserved permission `observability:read` in this codebase is an unapproved candidate and is not an IAM provisioning instruction.

Vault support is a real HashiCorp KV v2 HTTPS read boundary: set `SCB_VAULT_ENABLED=true`, `SCB_VAULT_ADDRESS` (approved HTTPS URL), `SCB_VAULT_MOUNT` and `SCB_VAULT_STARTUP_CHECK_PATH`; inject `SCB_VAULT_TOKEN` through a protected secret mount/environment outside Git. These environment overrides take precedence over `vaulthc` YAML defaults. The startup checks a real read; no fake service, fallback credentials or successful external connectivity is claimed. Secret rotation, token revocation and lease management need on-prem verification. Avoid HTTP request/response payloads, authorization headers, principal identifiers and HR content in telemetry; only method, registered route template, status, duration and random request identifier are logged. Prometheus metrics require a verified signed permission; traces create spans using OpenTelemetry API but **no external exporter is configured/claimed**.

## Error handling and troubleshooting

- Invalid YAML/zone/issuer/audience/CORS: process fails immediately with generic `ConfigurationError`, no config or secret text.
- IdP JWKS unavailable: production startup fails; development `/ready` returns 503 and protected routes return 401.
- Unsupported algorithm, bad signature, expired/not-yet-valid/wrong audience: 401.
- Signed identity without required permission: 403.
- Request > configured limit: 413; rate limiter: 429; request deadline: 504. A multi-worker/multi-node rate limit is **not** enforced here and requires ingress/distributed enforcement. Use the reverse proxy for hard transport-level deadlines and upload limits.
- Inspect only sanitized structured logs; do not enable Uvicorn access logging with raw URL queries in production.

## Rollback, release and verification gates

Stop instances, revert to a known-good image by immutable image digest, restore approved secrets/config, rerun liveness/readiness and negative authorization tests. For Git history, use a forward revert commit; never force push. There are no database migrations or Qdrant collections in Phase 02. Still pending: end-to-end IdP/SSO, Vault, TLS/rotation, firewall deny tests, distributed rate limiting, metrics/tracing exporter, CI run evidence, SBOM/vulnerability approval, load, HA and restore drills. Record each command, runner/platform, SHA, owner decision and sanitized output before upgrading phase status.

## Security remediation — JWKS, deadlines, rate limits (2026-10-24)

- A single per-process background refresh task fetches approved JWKS every 60 seconds after startup. Trusted keys are considered fresh for five minutes; if the IdP stays unavailable beyond this TTL, readiness returns 503 and token validation fails closed.
- JWKS fetches from unknown kid headers and stale caches share a lock and 15-second refresh-attempt cooldown, including failed attempts. A real key rotation may therefore take up to 15 seconds to become accepted; obtain IAM sign-off and measure rotation and outage behavior with the actual organization IdP.
- HTTP timeouts before response headers return 504. After response headers have begun, the ASGI request is aborted to avoid a protocol-invalid second response. The ingress must close incomplete requests and enforce upstream deadlines.
- Expired IP buckets are cleaned before the 10,000-client capacity test. Limits are still per process and use the socket peer. Do not trust client-supplied X-Forwarded-For; distribute limits through an approved ingress configuration and trusted-proxy list (open D-01/D-07).
- Windows PowerShell 5.1: the smoke-test Invoke-WebRequest command uses -UseBasicParsing to avoid interactive HTML parsing prompts.
- Pinning the base image by an approved digest, transitive dependency hashes, and configuring an on-prem trace exporter require approved supply-chain and operations decisions. Neither is represented as completed in this remediation.

## HTTP framing remediation and test command (2026-10-24)

Requests with bodies are bounded by the configured `server.max_request_bytes` regardless of method. Duplicate Content-Length, simultaneous Content-Length/Transfer-Encoding and mismatched declared/actual body lengths yield HTTP **400**, while an actual body above the limit yields **413**. Small multi-frame request bodies are aggregated and replayed as one ASGI request event. Gateway-provided transport validation and TLS remain mandatory.

The newly added ASGI tests are in `tests/test_phase02_http_edge_cases.py`. For an existing Windows checkout (in the directory containing `.git`), run `git pull --ff-only`, check `git rev-parse HEAD`, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
.\.venv\Scripts\pip-audit.exe -r requirements.txt --strict
```

Expected current CI baseline: **32 pytest PASS**, one known non-blocking framework warning. Do not mark owner Windows validation PASS until the actual updated PowerShell transcript is supplied.
