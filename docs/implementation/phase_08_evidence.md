# Phase08 — Technical evidence register, 2026-10-27

**Authorization:** owner instructed to progress Phase08; this is development authorization only. Draft PR stacked on unmerged Phase07. No Phase07/Phase06/Phase05 closure.

**Initial implemented scope:** pure query normalization and deterministic RRF, owner/domain/zone/version-based authoritative PostgreSQL recheck, Qdrant candidate payload validation and test-only synthetic dense probe without HTTP exposure. Actual Qdrant and PostgreSQL negative tests are included in CI.

**Tests A Executed + Actual Results:** PENDING first Phase08 PR-head CI.
**Tests B Executed + Actual Results:** PENDING real isolated Qdrant/PostgreSQL CI; any synthetic `published` fixture is not a Phase07 approval and synthetic input numeric vectors do not establish actual Embedding.
**Tests A/B Required but Missing:** actual versioned Embedding/Reranker and lexical provider, model selection D-03 and D-04, Gold Set and D-12 benchmarks, approved publish/revoke/index alias and durable recovery Phase07, reranker timeout/abstention/context real tests and independent technical assessment.
**Tests C Deferred to Phase18:** `P18-P08-C01..C06` all DEFERRED_TO_PHASE_18, NOT_RUN and NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P08-C01, C02, C03, C04, C05, C06.
**Technical DoD Status:** `IN_PROGRESS — NOT_SATISFIED`.
**Phase Status Before/After:** `NOT_STARTED → IN_PROGRESS`.
**Production Release Status:** `NOT_READY`.

## Verified source-specific Group A/B results — 2026-10-27

**Exact tested implementation SHA:** `55faa70beee768c749294016853cf8ea8611e69d`
**Actual completed GitHub CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40504920953 — all **6/6 SUCCESS**: verify, qdrant-integration, postgres-integration, ingestion-integration, docker-build, secret-scan.

**Tests A Executed + Actual Results:** compile/import/pytest and unit/security/negative/regression **108 PASSED / 31 SKIPPED / 2 warnings**; Ruff Check/Format PASS, strict pip-audit `No known vulnerabilities found`, SBOM generated, Docker image build and secret-scan SUCCESS. SKIPPED is not PASSED.

**Tests B Executed + Actual Results:** real isolated authenticated Qdrant Phase04 **9 PASSED**, Phase07 synthetic unpublished staging **1 PASSED**, Phase08 synthetic scoped candidate/deny-all policy probe **1 PASSED**. Genuine disposable PostgreSQL Phase08 authorization/revoke regression **1 PASSED** (test-only manual `published` fixture, NOT verified Phase07 publication), inherited live S3/ClamAV/PostgreSQL ingestion **13 PASSED**, real Persian/Arabic OCR synthetic Gold Fixtures **2 PASSED** (CER=0.000 on the limited fixtures only), true dependency outages/recovery **8 PASSED**, PostgreSQL prior regression **4 PASSED**. Existing migration upgrade/repeat/drift/test-only reverse/re-upgrade checks are included in successful integration jobs.

**Prior unsuccessful runs preserved as evidence, NOT relabeled success:** initial CI https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40504365806 had Ruff isort failure and a Phase08 test fixture FK insert-order failure. After both changes CI https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40504684041 passed the real Phase08 PostgreSQL test but `verify` still failed on Ruff formatting. Corrected formatter differences and source-matched final run 40504920953 passed **all six jobs**.

**Tests A/B Required but Missing:** real version-pinned D-03 query encoder and Reranker model lifecycle/timeout, actual approved sparse/lexical path and D-04 decision, Phase07 approved publication job/manifest/atomic visibility and real indexed evidence, real Dense vs Lexical vs Hybrid vs Rerank benchmark against an annotated authorized Persian Gold Set, D-12 acceptance criteria, negative contradictory/outdated evidence/abstention tests and accountable independent technical/security approval. Until these are present, Phase08 technical DoD **NOT SATISFIED**.

**Tests C Deferred to Phase18:** `P18-P08-C01..C06` each `DEFERRED_TO_PHASE_18`, not executed and not passed.
**Phase 18 Verification Register IDs:** P18-P08-C01, P18-P08-C02, P18-P08-C03, P18-P08-C04, P18-P08-C05, P18-P08-C06.
**Technical DoD Status:** `INITIAL_ENGINEERING_AB_VERIFIED — FULL_SCOPE_NOT_SATISFIED`.
**Phase Status Before/After:** `NOT_STARTED → IN_PROGRESS`.
**Production Release Status:** `NOT_READY`.

Subsequent evidence-only commits are not asserted to be the same source SHA. Any exact final branch HEAD can be checked in its own CI run.
