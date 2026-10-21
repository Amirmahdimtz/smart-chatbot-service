# ADR-0004 — Controlled Phase 02 development gate

- Date: 2026-10-21
- Status: AUTHORIZED_FOR_DEVELOPMENT_ONLY; formal stakeholder approvals pending
- Baseline: `c5e40aaaca4316620ddeba2b5c260396e3c9263f` on `main` (public repository)

## Context

Phase 01 is `IMPLEMENTED_AWAITING_VERIFICATION`: G-01 through G-07 lack owner sign-offs, and G-08 has owner-reported Windows tests but still awaits technical verifier approval. The project owner explicitly authorized a `GO_FOR_DEVELOPMENT` continuation to Phase 02 without falsely closing Phase 01. This permission is not an architecture/security/production approval.

## Decision

Implement independent runtime and security boundaries now, on a forward-only `main` commit as expressly authorized. Preserve Phase 01 contracts and approval gates unchanged. Deny non-public HTTP access without a valid RSA-signed JWT and an explicit signed permission; do not invent organization IdP, identity mappings or RBAC/ABAC policy grants. Use an exact configured issuer, audience and JWKS URL per deployment; each deployment must have independently configured credentials/identity, with no shared HR/agent/database connectors. Default to no Identity Provider in development, causing readiness to be unavailable and protected routes to reject requests. Require approved IdP and Security Owner tests before production rollout.

## Open decisions and effect

| Decision | Phase 02 independent deliverable | Dependent condition / evidence |
|---|---|---|
| D-01 | Request guard and per-process rate limiter | Peak/QPS traffic benchmark; distributed ingress quotas |
| D-05 | Process lifecycle and Docker build | Approved HA topology and failure drills |
| D-07 | JWT/JWKS RS256 validation | IAM-signed issuer/audience/claim mapping, JWKS reachability and rotation E2E |
| D-08 | Explicit server-side permission guard | Signed role-to-permission and purpose/ownership/classification policy |
| D-15 | Separate environment config/network | Inference isolation decision and network deny probes |
| D-16 | Health/readiness/metrics API only | Domain/client API contracts before later phases |
| D-18 | CI workflow scaffold | Repo governance, CI runner/branch protection owner approval |

## Consequences

No Phase 01 closure marker is issued. Production readiness is prohibited until actual SSO, secrets, ingress/proxy, network segregation, monitoring, CI and security sign-off have evidence. Public GitHub must contain no secrets, staff names, internal systems or real data. Revert forward with another reviewed commit if necessary; never force-push. A historical secret exposure requires incident response and rotation rather than a simple revert.
