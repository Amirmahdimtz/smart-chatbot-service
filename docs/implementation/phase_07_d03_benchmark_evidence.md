# Phase07 D-03 — Actual embedding comparison evidence register

Date: 2026-10-28
Status: BENCHMARK_PREPARED / EXECUTION_PENDING

**Branch:** `feat/phase07-d03-evaluation` stacked on Phase07 PR #5; the Phase06 defect remediation PR #8 is separately Draft and must be reconciled by review. There is no approved D-03 selection.

**Dataset:** `benchmarks/phase07/gold_synthetic_v0.1.json` — synthetic seed (18 documents, 20 questions, 17 labeled positives), **NOT expert-reviewed Gold**. Missing actual domain Gold, multi-annotator labeling and accepted quality thresholds; NO fake metrics are allowed.

**Candidates:** `intfloat/multilingual-e5-small` and `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, both pinned to HF full commits; license, safetensors SHA, RAM and true CPU inference captured by `benchmarks/phase07/run_real_embedding.py` only after actual model load. Distinct `query:` / `passage:` prefixes for E5. License metadata declarations are NOT legal approval.

**Tests A Executed + Actual Results:** pending exact PR-head CI; `tests/test_phase07_benchmark_metrics.py` validates scoring and scope constraints.
**Tests B Executed + Actual Results:** pending actual GitHub Actions `Phase07 Real CPU Embedding Benchmark` separate two-candidate matrix. No scores, inference PASS, latency or RAM claimed before observing successful workflow and artifacts.
**Tests A/B Required but Missing:** independently approved D-03 model decision, actual domain Gold and thresholds, remaining Phase07 real Embedding Provider, durable indexing and publish/revoke integration, evaluation repeatability, legal and reviewer approval.
**Tests C Deferred to Phase18:** P18-P07-C01..C07, NOT_RUN/NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P07-C01, C02, C03, C04, C05, C06, C07.
**Technical DoD Status:** IN_PROGRESS / NOT_SATISFIED.
**Phase Status Before/After:** IN_PROGRESS → IN_PROGRESS.
**Production Release Status:** NOT_READY.

A failed CI candidate model download, checksum, dependency or inference must be reported `BLOCKED_OR_FAILED`; it is not a successful benchmark.


## Actual CI observations for this attempt — 2026-10-28

**PR #10:** https://github.com/Amirmahdimtz/smart-chatbot-service/pull/10 (Draft). PR #9 was closed as superseded, unmerged.

**Previous run (source SHA `69ba95d29a98569a3fb0102f80ae07ea30a6c0e4`):** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40644869102 — original `verify` Python tests **106 PASSED / 29 SKIPPED**, `ruff check` PASS, but **`verify` overall FAILED on Ruff formatting** of the benchmark metrics test. Formatting has been corrected in subsequent code (SHA `e7dac72888b51ecb3866e5d4dbde502471cb77e1`). An unsuccessful workflow cannot be represented as an A PASS.

**Execution blocker:** As of this evidence entry, no GitHub Actions workflow run was returned for the newer source HEAD `5ae2e14a08e6184a624ad5254e1a3616eb601ffd` despite adding the real CPU matrix to the existing Foundation workflow and opening Draft PR #10. Therefore **NO actual model weight download/inference result is evidenced**, neither candidate has real measured Recall/latency/RAM, and the comparison job has not been observed. Its cause is not independently established; possible GitHub event/Actions approval/routing limitations require inspection through the repository Actions UI or an owner-triggered branch push. Do not label this as a successful B benchmark.

**Tests A Executed + Actual Results:** old SHA 106 PASSED / 29 SKIPPED, Ruff formatting FAILED. Latest code A run NOT_OBSERVED.
**Tests B Executed + Actual Results:** NO D-03 candidate model inference runs observed, B evaluation BLOCKED_EXTERNAL_PENDING_CI_EXECUTION. Inherited existing real PostgreSQL/Qdrant test results from earlier phases are not Embedding model evidence.
**Tests A/B Required but Missing:** genuine both model CPU inference and weights SHA recorded by CI, accepted domain Gold Set with independent annotation, D-03 informed decision and approval, actual Indexing/Publication provider and recovery B tests.
**Tests C Deferred to Phase18:** P18-P07-C01..C07 all DEFERRED_TO_PHASE_18 / NOT_RUN.
**Phase 18 Verification Register IDs:** P18-P07-C01, C02, C03, C04, C05, C06, C07.
**Technical DoD Status:** NOT_SATISFIED; EVALUATION_HARNESS_IMPLEMENTED / ACTUAL_MODEL_B_NOT_VERIFIED.
**Phase Status Before/After:** IN_PROGRESS → IN_PROGRESS.
**Production Release Status:** NOT_READY.

The executable deliberately emits `BLOCKED_OR_FAILED` without metrics upon any model error and the aggregator requires two genuine success artifacts. No test fixture or synthetic numerical vector counts as actual Embedding model execution.
