# ADR-0005 — Conditional technical entry gate for Phase 03

- Date: 2026-10-24
- Status: **TECHNICAL_GO_FOR_DEVELOPMENT_ONLY**; no Production or stakeholder-security approval
- Baseline source: `f01862d66e67c547df1638cc80fdd931bac1b3da`, `main`
- Evidence: [Phase 02 CI run 40072315115](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40072315115), 32 pytest PASS, verify/docker-build/secret-scan success
- Related: [ADR-0004](ADR-0004-phase02-development-gate.md), [Phase 02 evidence](../implementation/phase_02_evidence.md), [Phase status](../implementation/progress.md)

## Context

The approved project plan states that Phase 03 (PostgreSQL operational schema and migrations) depends on Phase 02. Source-level foundation, HTTP security, runtime, auth denial, DI, CI, release scaffolding and regression tests have been implemented and have current CI evidence. Phase 01 and Phase 02 **are not CLOSED**: real IdP/SSO, Vault, separate public/internal test deployments with independent credentials, gateway/network isolation, observability endpoints, operational recovery and responsible-owner signatures are not yet evidenced. The earlier Phase 02 exception (ADR-0004) did not silently waive these requirements.

## Decision and limits

**Technical review grants a conditional GO for Phase 03 independent development only.** It is *not* approval to initiate Phase 03 automatically, change organizational databases, process HR/PII, deploy to production, or waive Phases 01/02 acceptance. The project owner must explicitly command Phase 03 initiation; at that time verify live main SHA and dependencies.

Permitted only after the explicit start command:
- Review existing PostgreSQL assets, decide an ERD/schema and migration/rollback contract with the proper owner, then implement minimal Phase 03 models, PsqlDbContext, repositories and Alembic on an **isolated development PostgreSQL database with synthetic data**.
- Maintain constructor DI and four-layer architecture; require actual PostgreSQL integration tests and rollback/recovery verification. Do not invent organization schema or retention policy.
- Ensure all future database and HTTP access remains AuthZ-controlled; **do not introduce any unapproved Public→Internal data connection**.

Hard stops and open gates:
- **No production or real internal/HR datasets** until data classification, retention and Security/HR Policy Owner approvals.
- **No migration against shared/non-disposable organizational databases** without separately approved schema, backup/restore procedure and change plan.
- **No status upgrade to CLOSED** for Phase 01 or 02 without original Definition of Done, on-prem tests and signatures; the Phase 02 on-prem identity/network and authorized-metrics acceptance remain open.
- Missing local Windows rerun of the five newly added HTTP framing tests must be recorded separately from actual CI success. Any failed regression or critical security finding blocks further Phase 03 advancement until corrected.
- Confirm D-01/D-05/D-07/D-08/D-15/D-18 ownership, explicit approvals or tracked deferrals; production network/gateway, digest/hashes and tracing exporter are unresolved.

## Outcome

Phase 01: `IMPLEMENTED_AWAITING_VERIFICATION`; Phase 02: `IMPLEMENTED_AWAITING_VERIFICATION`; Phase 03: `NOT_STARTED` until explicitly commanded. **Conditional technical development gate only**, no `PHASE_02_CLOSED` or `PHASE_03_STARTED` marker. If a later approval authority rejects the exception, halt Phase 03 work and reconcile through a new ADR; do not rewrite history.
