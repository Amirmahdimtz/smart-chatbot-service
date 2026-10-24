# Phase 04 — Independent Technical Acceptance (Qdrant)

- **Date:** 2026-10-24
- **Review type:** AI-assisted technical evidence/source review authorized by the project owner; **not** a Human Security/Infrastructure/Privacy/Release signature.
- **Decision:** `TECHNICAL_ACCEPTED / PHASE_04_CLOSED` **for Phase 04 isolated synthetic Qdrant foundation only**.
- **Source reviewed:** `29e846070dd1089321520222b39688219a5e7cb2` on `feat/phase04-qdrant`; reference baseline `0b34f457bacfe4aba704ff01563fcd1c4e62a97c`.
- **CI:** [Run 40091297919](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40091297919) — **5/5 completed jobs SUCCESS**.
- **Phase Status Before:** `NOT_STARTED` → `IN_PROGRESS` → **`CLOSED` technical**, subject to merging this tested code and documentation into the reference branch. This is not Production approval.

## Source and architecture review

The Qdrant-specific code respects `Host → Application → Core → Infrastructure` conventions; Infrastructure holds Qdrant network I/O, while an existing auto-discovered FastAPI health controller only requests readiness. Provider is a singleton discovered through `@inject`; injected ConfigReader/Vault; lazy opt-in startup; single reused AsyncQdrantClient with safe shutdown. Qdrant is disabled by default.

Configuration enforces exact deployment zone, either env-injected or Vault secret, configurable non-final dimension/distance, loopback-only plaintext in development/integration and TLS elsewhere; malformed secrets/endpoints are not emitted in mapped exceptions. No Qdrant endpoint/API is exposed to end users.

Collections are zone-specific, schema-versioned and validated before reuse. Existing wrong-dimension or incompatible indexed payload types are rejected. Payload indexes cover zone/domain/doc/classification/publication; UUIDv5 deterministic point IDs, bounded batch preflight, wait-confirmed upsert/delete, explicit alias switching and synthetic snapshot creation were implemented. Qdrant queries demand non-empty trusted document UUID allowlist and classification/domain scope, plus published metadata. **Qdrant does not grant authorization**: consuming Core must re-check Postgres/policy metadata and publication before returning results. Phase 04 does not build RAG/ingestion/publication endpoints.

## Group A — executed results

On the exact review SHA, [CI run 40091297919](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40091297919):

| Check | Actual result |
| --- | --- |
| Compile/import + both Phase01 validators | PASS (`verify` job SUCCESS) |
| Full Pytest regression and Phase04 negative/contract unit | **43 passed / 5 skipped**, 1 existing Starlette deprecation warning |
| Ruff check | PASS |
| Ruff format --check | PASS; 28 files already formatted |
| pip-audit strict | PASS: `No known vulnerabilities found` |
| CycloneDX SBOM generation/upload | PASS |
| Docker image build | PASS |
| gitleaks secret-scan | PASS (`no leaks found`); two exact fingerprints of historical **synthetic, retired** Phase04 CI test values are documented in `.gitleaksignore`. Current test key is generated randomly on every CI run. No global secret-scan bypass. |

The 5 skipped tests are real service-specific tests not configured inside the generic verify job; the corresponding PostgreSQL and Qdrant real-server jobs executed them separately. Do **not** treat skipped tests as passes in that generic job. Earlier failed CI runs and root causes remain documented in [Phase04 evidence](phase_04_evidence.md).

## Group B — actual isolated live Qdrant and PostgreSQL

- Real **Qdrant Server v1.20.0 and Python SDK v1.20.0** using local Docker + ephemeral synthetic API key in `qdrant-integration`: **7 tests PASS**, including authenticated/wrong-key connections, collection creation, indexed payload scope, document/domain filters and denied empty filters, stable IDs, duplicate-batch and dimension rejection, all-or-none batch preflight on invalid vectors, upsert/delete/query, actual snapshot creation, reconnection/unavailability, bounded retry, **version 1 → 2 rebuild / alias cutover → version 1 rollback**, incompatible existing dimension and existing payload-index type rejection. It does not prove organizational snapshot restore or real IdP security.
- Real isolated **PostgreSQL 16.x** in `postgres-integration`: **4 tests PASS**, repeat Alembic upgrade, drift check, disposable test-only downgrade/re-upgrade PASS. This is regression evidence for Phase03 foundation, not a new PG schema.
- No actual On-Prem Qdrant/production secrets/organizational datasets were accessed.

## Group A/B Required but Missing

**None identified for the expressly authorized synthetic-only Phase04 technical scope.** There is no final embedding/schema freeze (D-03), Sparse/Hybrid fusion (D-04), real identity/publication policy (D-07/D-08), or future Phase07/08 retrieval/authorization E2E in this phase. Those remain explicitly open decisions or owning future phases; they are not falsely marked tested here.

## Group C Deferred to Phase 18

Unexecuted, not waived: `P18-P04-C01`–`P18-P04-C10`, all `DEFERRED_TO_PHASE_18`, recorded in [Phase18 register](phase_18_verification_register.md) with requirement, role owner, expected result and required evidence; covers Qdrant On-Prem hosts, Public/Internal network isolation, TLS/Vault/rotation, least-privilege credentials, multi-node snapshot/restore, HA/DR, load/soak/capacity, model-to-index fit, authorized publication E2E, and final operational security/UAT.

## Technical DoD and final boundaries

- **Technical DoD Status:** PASS for limited Phase04 structural/vector infrastructure with synthetic data; no unresolved critical flaw identified in reviewed A/B scope.
- **Technical Acceptance Decision:** `TECHNICAL_ACCEPTED` (AI-assisted, no organization Security/Release signature).
- **Phase Status Before/After:** `NOT_STARTED` / `CLOSED` (technical only; recorded after A/B verification).
- **Production Release Status:** `NOT_READY` — only Phase18 can authorize `PRODUCTION_READY`.
- **Next Eligible Phase:** Phase05 **only after the owner's separate explicit command**. Phase15 Agent remains `BLOCKED_EXTERNAL`.
