# ADR-0007 — Conditional technical entry approval for Phase 04 (Qdrant)

- **Date:** 2026-10-24
- **Decision:** `CONDITIONAL_GO_FOR_DEVELOPMENT_ONLY`
- **Scope:** Phase 04 — Qdrant Secure Deployment & Search Provider; isolated development and technical verification only
- **Basis:** owner-uploaded `Smart_Chatbot_Implementation_Plan_FA.md` **v1.1.0** (§§0.3–0.6, §8, Phase 04, Phase 18); `Service_Architecture_Guide_FA.md`; [ADR-0006](ADR-0006-phase-closure-verification-v1_1_0.md)
- **Reviewed repository:** `Amirmahdimtz/smart-chatbot-service`, `main` at `ce3def7094bafbd505dd51e4059b285ae7852d09`.
- **Evidence:** Phase 03 [technical acceptance](../implementation/phase_03_technical_acceptance.md), [progress](../implementation/progress.md), [Phase 18 Register](../implementation/phase_18_verification_register.md), [GitHub Actions run 40088290757](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40088290757) (verify/postgres-integration/docker-build/secret-scan: **4/4 successful**).
- **Review type:** AI-assisted independent technical entry decision requested by the project owner. It is **not** an organization Infrastructure, Security, Data Owner or Production Release signature.

## Preconditions and actual state

| Dependency | Observed state | Impact on Phase 04 |
| --- | --- | --- |
| Phase 01 requirements and architecture baseline | `IMPLEMENTED_AWAITING_VERIFICATION`; G-01–G-08 decisions/signatures remain unresolved | Approved *independent technical development only*; does not waive approvals needed for real organizational data/architectural decisions |
| Phase 02 secure runtime/DI/config/security foundation | `IMPLEMENTED_AWAITING_VERIFICATION`; prior code/CI evidence, organization IdP/Vault/isolation not verified | Reuse actual source conventions, fail-closed behavior and synthetic identities; no assertion of production SSO or physical isolation |
| Phase 03 PostgreSQL structural foundation | **`PHASE_03_CLOSED` — technical only**, real synthetic PostgreSQL tested; `0001_foundation` migration | Necessary structural dependency is technically available for isolated Phase 04 |
| Phase 03 organizational acceptance | **Six Group C items `P18-P03-C01`–`C06` deferred to Phase 18** | Not a Phase 04 development blocker; not PASS and not permission for production |
| Phase 04 implementation | **`NOT_STARTED`**; no Qdrant provider module currently present in `src/infrastructure` | This decision **authorizes entry only**, does not implement/start phase |

## Decision

**Grant technical entry approval for Phase 04 development after the owner's separate, explicit start instruction.** This is an exception for the independent and testable Qdrant infrastructure scope while earlier Phase 01/02 formal decisions remain open; the exception is **not** a retroactive `CLOSED` decision for those phases and does not waive their required technical/policy evidence.

**Permitted work after explicit start:** inspect current source and DI/config conventions; select and pin compatible Qdrant server/client versions with source-verified SDK calls; add opt-in, zone-scoped Qdrant configuration and real Infrastructure provider; use isolated Qdrant instances/credentials and synthetic vectors; define configurable schema/vector dimension without claiming final embedding-model decision; implement secure batch upsert/query/delete, deterministic point IDs, collection/alias version contracts, health, timeouts, bounded retries, lifecycle/disposal, snapshot/rebuild and recovery documentation.

**Required Phase 04 Group A/B evidence before technical `CLOSED`:**
- Existing full CI regression, lint/format, compile, contract/negative/security tests, dependency audit and secret scan; actual outcomes and commit SHA.
- **Real Qdrant server integration** using Docker/CI or other authorized isolated service, synthetic data and nonproduction credentials (a Mock-only test is insufficient): authenticated connection and wrong-key/denied-access, collection creation/versioning, scoped payload filters, stable point ID, upsert/retrieve/delete, batch partial failure, timeout and unavailable service, rebuild/snapshot/restore as technically appropriate.
- Deny-by-default for cross-zone/classification/unauthorized data; no direct client bypass. Check with actual source/metadata and avoid claiming an unapproved real IdP.
- Record `Tests A/B Required but Missing` without marking unexecuted tests passed. Required technical dependencies and critical security defects cannot be deferred to Phase 18.

**Group C / Phase 18:** organization Qdrant host and networking, real Public/Internal physical segmentation, Vault/TLS/credential rotation, multi-node backup/restore, GPU/model-driven schema and actual capacity/load/HA/DR remain `DEFERRED_TO_PHASE_18`. Add individual immutable IDs with owner, requirement, expected result and evidence to the shared verification register during Phase 04. Deferral does not grant release approval.

## Explicit boundaries and hard stops

1. Do not connect to organization Qdrant/HR data, real credentials, shared databases or production networks without separate owner/security permission. No deployment, data publishing or `PRODUCTION_READY`.
2. **D-03** (embedding model/dimension) and **D-04** (sparse/fusion architecture) are open: synthetic test-vector dimensions may be used in isolated fixtures, but no irreversible or final production collection schema may be invented.
3. **D-07/D-08** identity, classification, retention and publication-policy approvals remain open; no public/internal exposure of real documents and no bypassing current PostgreSQL publish-state semantics.
4. No premature implementation of Phase 05 ingestion, Phase 07 embedding/index publication, Phase 08 ranking/RAG or Phase 09 generation; only Phase 04 infrastructure scope.
5. `Phase 04 Status Before = NOT_STARTED`; **after this gate decision it remains `NOT_STARTED`**. A separate owner command “فاز ۴ را شروع کن” is required to initiate implementation.
6. `Phase 01/02 Status` unchanged. `Phase 03 Status = CLOSED (technical)`. `Production Release Status = NOT_READY`.

## Outcome and authorization

- `Technical Entry Gate: CONDITIONAL_GO_FOR_DEVELOPMENT_ONLY` — **APPROVED** for independent Phase 04 development after explicit owner start.
- `Phase 04 CLOSED: NO`. Actual Qdrant development, integration and acceptance tests have **not been executed**.
- `Production Release: NOT_READY`; Group C tests only in Phase 18.
