# Phase 02 threat model and verification record

| Threat | Current control | Evidence / remaining risk |
|---|---|---|
| Forged bearer identity and `alg=none` | RS256-only signature, fixed issuer/audience/time checks | Isolated RSA test keys and negative tests; live IdP claim contract D-07 unapproved |
| HTTP user/role spoofing | Reject client identity headers, never map client metadata to Principal | Unit/ASGI negative tests |
| Cross-zone access | Deployment-specific audience and zone config; independent container networks | Wrong-audience test; **external firewall, network and credential separation NOT RUN** |
| Privilege escalation | Explicit permission claim requires valid signed bearer, default deny | 401/403 tests; permission assignment and ABAC D-08 pending |
| Secrets and PII in logs | No body/token/query/subject metrics or telemetry labels; generic config and HTTP errors | Code review/test patterns; production log retention and audit review NOT RUN |
| Invalid deployment configuration | Pydantic schema, HTTPS JWKS, no wildcard CORS, no default nondev identity | Negative tests; TLS certificate validation E2E NOT RUN |
| SSRF against JWKS/Vault | Operator-controlled URLs only, HTTPS required, no redirects, `trust_env=False`, short timeout | Code review; DNS/network egress allowlist pending |
| Abuse/slow requests | Bounded body buffer, in-process rate limit, per-call timeout | Local ASGI tests; distributed edge controls, load and stress pending |
| JWKS outage/rotation | Cached trusted keys, bounded cache TTL, unknown `kid` triggers refresh, fail closed on refresh errors | Simulated JWKS tests; real rotation/outage NOT RUN |
| Agent/data-source leaks | No Qdrant/HR/Agent connectors or domain endpoints introduced in Phase 02 | Repository discovery; later-phase mandatory access checks |

**Security signoff:** AWAITING_APPROVAL. The repository is public; disclosure review and branch rules D-18 are outstanding. No runtime integration is considered production-certified.
