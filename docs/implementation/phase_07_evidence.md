# Phase07 — Initial engineering evidence register

**Status:** IN_PROGRESS; no independent technical acceptance; Phase05/06 predecessor statuses unchanged.

**Preliminary implemented scope:** deterministic pre-publication manifest; strict finite/dimension/ordinal/checksum validation; indexed vector staging with `published=False` using Phase04 QdrantProvider; standalone true PDF page-offset fix in dependent branch; negative/unit and disposable Qdrant integration tests. Current source of truth for actual outcomes is GitHub Actions on the Phase07 Draft PR HEAD, not file creation.

**Tests A Executed + Actual Results:** pending exact PR-head CI review.
**Tests B Executed + Actual Results:** pending exact PR-head Qdrant CI review; real Persian embedding model, model benchmark, PG index job, publication and reindex tests NOT_RUN.
**Tests A/B Required but Missing:** P07-B02..B08; pending D-03 model evaluation, D-04 sparse strategy, Phase06 source-span upstream acceptance, D-07/D-08 data policy, full security technical acceptance.
**Tests C Deferred to Phase18:** P18-P07-C01..C07, NOT_RUN/NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P07-C01, C02, C03, C04, C05, C06, C07.
**Technical DoD Status:** IN_PROGRESS / FULL_SCOPE_NOT_IMPLEMENTED.
**Phase Status Before / After:** NOT_STARTED → IN_PROGRESS.
**Production Release Status:** NOT_READY.

This is only a phase kickoff. Test fixtures use synthetic vectors and are **not a substitute for a real embedding provider**. No model weight access, corpus benchmarks, final approvals, published vectors or Production Release are asserted.

## Exact source-matched A/B verification — 2026-10-27

**Tested source SHA:** `e4e4bc522470402089e97f8e9842011ed759dc20`
**Actual CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40482953105
**Result:** all SIX required jobs `SUCCESS`: verify, qdrant-integration, postgres-integration, ingestion-integration, docker-build, secret-scan. Earlier same-branch CI [40482772838](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40482772838) failed the verify job solely at three Ruff format differences; it remains a recorded failed run and is not considered a PASS. All were fixed in the source-matched successful run.

**Tests A Executed + Actual Results:** compile/discovery and core/unit/negative/regression: **103 PASSED / 29 SKIPPED / 2 warnings**; Ruff Check/Format **PASS**, strict pip-audit **PASS** (No known vulnerabilities found), SBOM, Docker build/non-root and secret scan jobs **SUCCESS**. The multipage source-span regression and new prepublication contract checks are included in the 103 tests. SKIP is NOT PASS.

**Tests B Executed + Actual Results:** real isolated authenticated Qdrant prior-regression **9 PASSED** and Phase07 unpublished staging/replay/query-denial **1 PASSED** (test uses *synthetic numeric vectors*, not actual model embeddings). Real isolated S3+ClamAV+PostgreSQL ingestion regression **13 PASSED**, actual Persian and Arabic OCR fixtures **2 PASSED** (each CER 0.000 for these synthetic fixtures only), reversible and cold-restart/recreate outage regression **8 PASSED**, real PostgreSQL regression **4 PASSED**, actual migration upgrade/drift/reversible test-only downgrade/reupgrade **SUCCESS**. No organization system used.

**Tests A/B Required but Missing:** B02..B08 model candidates/actual embedding runtime, D-03 signed selection, sparse/hybrid D-04 evaluation, durable index jobs/manifest PG state and fencing, partial Qdrant outage and consistency replay, safe versioned reindex/alias rollback, authorized atomic visible version, revoke-first/no stale citations, attributable expert acceptance. A/B full Phase07 DoD therefore remains **NOT SATISFIED**.

**Tests C Deferred to Phase18:** `P18-P07-C01` through `P18-P07-C07` all DEFERRED_TO_PHASE_18, NOT_RUN, NOT_PASSED.

**Technical DoD Status:** `INITIAL_ENGINEERING_AB_VERIFIED — FULL_SCOPE_IN_PROGRESS`.
**Phase Status Before/After:** `NOT_STARTED → IN_PROGRESS`.
**Production Release Status:** `NOT_READY`.
Further evidence-only documentation commits may advance branch HEAD without changing tested code; each exact code SHA/CI is explicitly identified above.
