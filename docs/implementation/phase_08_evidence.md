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
