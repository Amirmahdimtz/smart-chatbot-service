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


## Bounded handoff to dependent Phase09 development — 2026-10-27

**Exact Phase08 enhanced source SHA:** `65128df11e7c51f7b74937113c2c4784d714e099`; **actual completed CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40508470092 — **6/6 SUCCESS**. A: **111 PASS / 31 SKIP**, compile, Ruff, strict pip-audit, SBOM, Docker and Gitleaks SUCCESS. B: inherited isolated Qdrant/PG/S3/ClamAV/real OCR/Recovery test suites successful; no new real model benchmark executed.

Implemented one further dependency-independent A-slice: deterministic `EvidenceWindow` keeps whole validated canonical excerpts, rejects checksum/provenance contradictions, enforces max chunks/chars and returns `no_authorized_evidence` / `evidence_over_budget` hints. It does NOT detect semantic contradictions or stale facts and does NOT demonstrate any real Reranker. Model-dependent Phase08 B03–B08, D-03, D-04 and D-12 evidence remain REQUIRED/MISSING; independent technical acceptance is also missing. No Phase08 `CLOSED` decision, no merge. A stacked Phase09 development branch may start from this point because its independent prompt/citation contracts can be implemented without a live model, **not** because Phase08 is complete.

**Tests C Deferred to Phase18 / IDs:** `P18-P08-C01..C06`, NOT_RUN, NOT_PASSED.
**Technical DoD:** `PARTIAL_A_B_VERIFIED — MODEL_DEPENDENCIES_BLOCK_FULL_DOD`.
**Phase Status Before/After:** `IN_PROGRESS → IN_PROGRESS`.
**Production Release:** `NOT_READY`.
