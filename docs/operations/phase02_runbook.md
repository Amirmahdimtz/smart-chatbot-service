# Phase 02 — Runtime, security and operations runbook

## Status and prerequisite

This release provides HTTP runtime foundation and authentication/authorization enforcement only. It does **not** provide chat, database, Qdrant, AI models or Agent functions. Phase 01 has not been formally accepted. Default `development` deliberately has no IdP: `/live` and `/startup` return 200 but `/ready` returns 503 until valid JWKS configuration exists. Do **not** treat health-only startup as an application ready for production.

## Local Windows PowerShell

```powershell
git clone https://github.com/Amirmahdimtz/smart-chatbot-service.git
cd smart-chatbot-service
git switch main
git pull --ff-only
git rev-parse HEAD
git status --short
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m compileall -q src tests scripts
python scripts/validate_phase01.py
python -O scripts/validate_phase01.py
python -m pytest -q
ruff check src tests
ruff format --check src tests
$env:SCB_ENV = 'development'
$env:SCB_ZONE = 'public'
python -m uvicorn src.host.app:app --host 127.0.0.1 --port 5000 --no-access-log
```

In a second PowerShell window run:

```powershell
Invoke-WebRequest http://127.0.0.1:5000/api/v1/health_check/live
try { Invoke-WebRequest http://127.0.0.1:5000/api/v1/health_check/ready } catch { $_.Exception.Response.StatusCode.value__ }
try { Invoke-WebRequest http://127.0.0.1:5000/api/v1/health_check/metrics } catch { $_.Exception.Response.StatusCode.value__ }
```

Expected without configured IdP: 200 / 503 / 401. If you have a **test** IdP and approved test issuer/audience, set `SCB_JWKS_URL` (HTTPS), `SCB_ISSUER`, `SCB_AUDIENCE` for an actual `/ready` 200. Never place real tokens in `.env` files or submitted logs. Stop with Ctrl+C; expected Uvicorn graceful shutdown.

Run `python -m pytest -q tests/test_phase02_runtime.py` for the isolated cryptographic test fixtures, and `git status --short` to confirm no untracked secrets. On issues, send sanitized exit status, test names, Git SHA and the first error stack **after removing tokens, identifiers, URLs and personal content**.

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

Vault support is a real HashiCorp KV v2 HTTPS read boundary: enabling `vaulthc.enabled` requires an approved address, mount, startup_check_path and `SCB_VAULT_TOKEN` injected by secret mount/environment outside Git. The startup checks a real read; no fake service, fallback credentials or successful external connectivity is claimed. Secret rotation, token revocation and lease management need on-prem verification. Avoid HTTP request/response payloads, authorization headers, principal identifiers and HR content in telemetry; only method, registered route template, status, duration and random request identifier are logged. Prometheus metrics require a verified signed permission; traces create spans using OpenTelemetry API but **no external exporter is configured/claimed**.

## Error handling and troubleshooting

- Invalid YAML/zone/issuer/audience/CORS: process fails immediately with generic `ConfigurationError`, no config or secret text.
- IdP JWKS unavailable: production startup fails; development `/ready` returns 503 and protected routes return 401.
- Unsupported algorithm, bad signature, expired/not-yet-valid/wrong audience: 401.
- Signed identity without required permission: 403.
- Request > configured limit: 413; rate limiter: 429; request deadline: 504. A multi-worker/multi-node rate limit is **not** enforced here and requires ingress/distributed enforcement. Use the reverse proxy for hard transport-level deadlines and upload limits.
- Inspect only sanitized structured logs; do not enable Uvicorn access logging with raw URL queries in production.

## Rollback, release and verification gates

Stop instances, revert to a known-good image by immutable image digest, restore approved secrets/config, rerun liveness/readiness and negative authorization tests. For Git history, use a forward revert commit; never force push. There are no database migrations or Qdrant collections in Phase 02. Still pending: end-to-end IdP/SSO, Vault, TLS/rotation, firewall deny tests, distributed rate limiting, metrics/tracing exporter, CI run evidence, SBOM/vulnerability approval, load, HA and restore drills. Record each command, runner/platform, SHA, owner decision and sanitized output before upgrading phase status.
