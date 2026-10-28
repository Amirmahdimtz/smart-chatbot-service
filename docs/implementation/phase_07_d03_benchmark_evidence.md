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
