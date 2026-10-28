# Phase07 — Durable Index Jobs, PG-authoritative publish and revoke: actual evidence

Date: 2026-10-28
Draft PR: https://github.com/Amirmahdimtz/smart-chatbot-service/pull/12
Depends on Draft PR #11 (real synthetic CPU→PG→Qdrant), itself dependent on #10 and #5; no merge or previous phase status change.

## Exact tested source and executable results

**Source code SHA:** `3467f0fac3209cb6a404fe19f4156c88fd9a3f4a`
**Actions:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40663124973 — **COMPLETED, 8/8 JOBS SUCCESS**: verify, postgres-integration, qdrant-integration, ingestion-integration, docker-build, secret-scan, and real e5-small and MiniLM-L12 model + PG/Qdrant integration jobs.

### Tests A Executed + Actual Results

- Actual Python general suite **108 PASSED / 31 SKIPPED / 2 warnings**, including unit test for blinded review export (not expert adjudication), migration metadata regression, and source contract tests.
- Ruff Check and Ruff Format PASSED, strict pip-audit `No known vulnerabilities found`, SBOM generated, Docker Build SUCCESS, Gitleaks Secret Scan SUCCESS.
- Earlier failed runs due to old exact metadata table expectation, an invalid wrong-token fixture and Ruff style are **FAILED**, not passed. Each was corrected before the source SHA above.

### Tests B Executed + Actual Results

- Two separate actual isolated CI environments with **real PostgreSQL 16, real authenticated Qdrant v1.20.0 and genuine pinned CPU safetensors**. Both E5-small and MiniLM-L12 job branches each reported `1 passed` for pre-existing hidden-source-model E2E and **`1 passed` for new durable job/publication/revoke E2E**. Neither is a fake model service.
- New genuine PostgreSQL + Qdrant test verifies `0004_index_lifecycle` migration, owner/domain restrictions, idempotent enqueue, immutable manifest JSON+SHA+point ID receipt, wrong token rejection, **expired lease reclaimed by a new token**, old token fencing and bounded retry, warmed real CPU embeddings, hidden Qdrant staging, distinct synthetic reviewer refusal for owner, digest mismatch refusal, explicit synthetic approval, Qdrant manifest verification and actual alias/point publication, PostgreSQL active-version pointer and published DocumentVersion, **PG-first revocation during simulated Qdrant disconnection**, durable `cleanup_pending`, cleanup on real Qdrant reconnection and zero published hits afterward.
- Dedicated real PostgreSQL and Qdrant regression jobs SUCCESS, inherited ingestion/OCR/service-outage tests SUCCESS. No corporate IdP, real data or hardware involved.
- Previous two-candidate benchmark over 18 synthetic snippets/20 queries (17 labeled positive) remains exactly that: a **synthetic smoke benchmark**, not accepted Persian/Arabic Gold, and cannot approve a D-03 winner.

## Truthful security/atomicity boundaries

- PostgreSQL `IndexPublication.active_version_id` and `DocumentVersion.state` are the *only* final read authority in the new design. The Qdrant `published` flag is a candidate filter, never authorization. PG cutover is atomic; **Qdrant mutation plus PostgreSQL transaction is NOT a distributed ACID transaction**. A Qdrant promotion can precede the PG state change: results must be re-authorized at retrieval/citation time against live PG. Failure compensation is best-effort. PG-first revoke blocks source authorization before eventual Qdrant cleanup.
- The current Phase08 reauthorization path was developed on a separate Draft PR and has not been reconciled with this newer `IndexPublication` table yet. Thus cross-phase **current-pointer read gate and no-stale-citation E2E remain REQUIRED A/B**, not passed.
- The synthetic test inserts a candidate DocumentVersion in `awaiting_approval` and explicitly supplies a second test reviewer. This is NOT a validated organizational IdP or approver authorization flow. The new service has no public HTTP endpoint. The reindex of two competing model/version generations and alias rollback under partial failure have not been acceptance-tested.
- Unreviewed `benchmarks/phase07/gold_synthetic_v0.1.json` includes author-proposed labels. `export_blinded_review.py` strips labels in the separate reviewer packet; **no two independent blind human annotations, adjudication, owner approval, legal permission or security sign-off have been received**.

## Tests A/B Required but Missing

1. Actual selected model (D-03) by *independently* approved Persian/Arabic/mixed Gold evaluation, legal and technical signoff, agreed thresholds (D-12); D-04 sparse/hybrid model selection.
2. Real Phase05 ingestion→durable index queue integration and policy-backed organizational approval (Group B with authorized synthetic organizational surrogate as available); actual role/permission enforcement beyond caller-supplied synthetic names.
3. Multi-version current-pointer cutover/reindex and rollback/reconciliation under injected Qdrant partial failure, competing publish/revoke race, expired max-attempt reclaim, cleanup outbox scanner/worker restart, cross-phase Phase08/09 authorization and citation freshness E2E.
4. Independent Backend/Architecture/Security review and actual quality evidence. Any critical security defect or missing genuine required integration blocks full technical closure.

## Tests C Deferred to Phase18 / Register IDs

`P18-P07-C01`, `P18-P07-C02`, `P18-P07-C03`, `P18-P07-C04`, `P18-P07-C05`, `P18-P07-C06`, `P18-P07-C07`: all `DEFERRED_TO_PHASE_18`, **NOT_RUN and NOT_PASSED**. No On-Prem GPU/IdP/Vault/network, load/stress, HA/DR or corporate security UAT demanded in Phases 01–17.

**Technical DoD Status:** `DURABLE_INDEX_PG_QDRANT_SYNTHETIC_A_B_VERIFIED — FULL_PHASE07_DOD_NOT_SATISFIED`.
**Phase Status Before/After:** `IN_PROGRESS → IN_PROGRESS`.
**Production Release Status:** `NOT_READY`.

This evidence appendix is a documentation-only commit after the exact code source SHA. Its *own* final HEAD CI must be checked independently before claiming 8/8 on the documentation commit.
