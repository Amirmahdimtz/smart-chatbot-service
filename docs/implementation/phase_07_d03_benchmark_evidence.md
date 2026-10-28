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


## VERIFIED REAL MODEL INFERENCE — two independent GitHub CPU CI runs, 2026-10-28

**Important correction to the historical observation above:** Earlier investigation relied on an API method that returns only `pull_request` runs, so it missed failing `push` workflow validation events. The separate new workflow initially generated failed zero-job push runs; restoring the known-good foundation workflow and adding a narrowly scoped CPU matrix to it enabled genuine `pull_request` inference. The invalid standalone workflow has now been deleted. The previous statement "no run observed" remains part of the historical timeline, but is **SUPERSEDED** by the following directly verified evidence.

**Exact source SHA for run 1:** `c7669d764eedcda135380f4192336db6fa824ee2` — [Actions #40655542808](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40655542808): **8/8 JOBS SUCCESS**.
**Exact source SHA for run 2:** `412ff5bfaccafe92734583106b364c4192108454` — [Actions #40655824049](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40655824049): **8/8 JOBS SUCCESS**. The second commit deletes the malformed standalone workflow but retains the same benchmark code and pinned models.
**Group A actual results for BOTH source SHAs:** `verify` Python **106 PASSED / 29 SKIPPED / 2 warnings**; Ruff Check/Format, compile, strict pip-audit (`No known vulnerabilities found`), SBOM, Docker image and Secret Scan SUCCESS. SKIP remains SKIP.

**Group B real CPU Embedding execution:** two different released public safetensors models, each loaded/warmed and used to generate full actual 384-dimensional vectors on isolated GitHub-hosted CPU. No stub/hosted embedding API/synthetic numeric model output. Both model jobs completed SUCCESS in each of the two runs. Real isolated PostgreSQL/Qdrant/Ingestion/Recovery regression jobs also SUCCESS.

| Indicator | intfloat/multilingual-e5-small | paraphrase-multilingual-MiniLM-L12-v2 |
| --- | --- | --- |
| Full immutable HF revision | `614241f622f53c4eeff9890bdc4f31cfecc418b3` | `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` |
| Real safetensors SHA-256 | `1a55775f53449dac10a2bcbc312469fac40b96d53198c407081a831f81c98477` | `eaa086f0ffee582aeb45b36e34cdd1fe2d6de2bef61f8a559a1bbc9bd955917b` |
| HF-declared license (NOT legal approval) | MIT | Apache-2.0 |
| Measured dimension / comparison metric | 384 / cosine | 384 / cosine |
| Recall@1 (17 relevant queries) | 0.941176 (both runs) | 0.941176 (both runs) |
| Recall@3 / Recall@5 | 1.000000 / 1.000000 | 1.000000 / 1.000000 |
| MRR@10 / nDCG@10 | 0.970588 / 0.978290 | 0.970588 / 0.978290 |
| Query CPU encoding p95 (run 1 / run 2) | 12.800 / 18.797 ms | 18.215 / 12.320 ms |
| Process RSS after inference (run 1 / run 2) | 1000.80 / 999.70 MiB | 987.61 / 989.64 MiB |
| Real model artifact ID (run 1 / run 2) | 12801252305 / 12800963737 | 12801482105 / 12801427067 |

Both runs used the **same actual dataset SHA-256** `fd6044e9aab75a00bb367d7edc1c72fdfcabc13c469578f4658e7a07d5645eff`, with 18 authored synthetic passages and 20 queries (17 positive, 3 zero-relevant excluded from retrieval quality). All four downloaded JSON artifact contents were inspected independently: each contained `status=EXECUTED_REAL_CPU_INFERENCE`, matching dataset hash, stable exact weights SHA within its model, repeatable quality outputs and actual measured latency/RSS. Group B actual model execution evidence: **PASSED for this narrow synthetic CPU benchmark only**.

**Critical interpretation:** On run 1 E5 query encoding p95 was faster, but on run 2 MiniLM was faster. Different GitHub CI runner hosts and only 20 single-query measurements mean no statistically defensible winner on latency, and identical high retrieval quality over 17 easy synthetic labels cannot establish D-03 selection. Both models are candidates for wider domain Gold benchmark. The single fa/ar and colloquial hard cases differ by model; expert labels and more adversarial mixed-script data remain essential. The three no-answer queries were **NOT** scored for abstention; the dense retrieval ranks something even for unsupported questions. Neither model was run through real Qdrant ANN, authorized publication/revoke or a selected Sparse pipeline. License metadata is NOT legal approval. No GPU/VRAM was measured.

**Tests A/B Required but Missing:** formal and independently reviewed permitted Persian/Arabic/mixed-domain Gold Set with actual relevance labels, more repeated/controlled CPU + approved D-03 decision, legal review, final Embedding Provider lifecycle, D-04 sparse/hybrid, real PostgreSQL/Qdrant durable indexing, approval, atomic publication/revoke and rollback, security review and accountable technical signoff. Final corporate On-Prem hardware tests remain Phase18 ONLY.
**Tests C Deferred to Phase18:** `P18-P07-C01..P18-P07-C07` all `DEFERRED_TO_PHASE_18`, NOT_RUN and NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P07-C01, C02, C03, C04, C05, C06, C07.
**Technical DoD Status:** `REAL_D03_SYNTHETIC_CPU_BENCHMARK_B_VERIFIED — PHASE07_FULL_DOD_NOT_SATISFIED`.
**Phase Status Before/After:** `IN_PROGRESS → IN_PROGRESS`.
**Production Release Status:** `NOT_READY`.
