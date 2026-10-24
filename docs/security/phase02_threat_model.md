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

## Remediation findings (2026-10-24)

- Idle-traffic JWKS expiry: a 60-second periodic task now refreshes trusted keys; five-minute TTL still fails closed during extended outages.
- Unknown-kid refresh storm: lock and 15-second fetch-attempt cooldown now bound refresh requests; actual IdP rotation remains a required external test.
- Mid-response timeout: aborts incomplete ASGI response instead of sending conflicting HTTP status; actual ingress behavior requires verification.
- Full IP cache: expired buckets are evicted before 10k capacity denial; proxy IP fairness and distributed edge limits remain open.
- Base image digest, transitive lockfile, monitoring exporter, IAM roles, and network zone isolation remain unapproved or unverified. No organizational sign-off is implied.

## Phase 02 second technical audit — HTTP framing (2026-10-24)

- **All-method request size enforcement:** GET, HEAD and OPTIONS are now subject to the same actual-stream payload cap as POST/PUT/PATCH/DELETE; Content-Length alone is not relied upon. CI regression covers an oversized chunked GET with absent Content-Length.
- **Memory boundedness:** many empty or tiny ASGI request events are coalesced into a single bounded request-body event before the application executes; CI regression verifies 2,000 empty frames do not create 2,000 retained event objects. An ingress transport-level timeout and buffering policy are still required for slow clients.
- **Framing ambiguity:** duplicated Content-Length, combined Content-Length/Transfer-Encoding or mismatch between declared and observed body length returns 400. This is defense in depth and does not replace an approved reverse proxy's HTTP request-smuggling safeguards.
- **Acceptance:** four earlier high-priority source defects and these newly identified HTTP framing gaps are covered by tests. Actual two-zone production-equivalent credential/network testing, audit retention and real IdP/Vault are still pending. **NO Phase 02 security or release sign-off has been issued.**
