# ADR-0014 — D-03: model-candidate evaluation protocol, no final model selection

Date: 2026-10-28
Status: PROPOSED / BENCHMARK_EXPERIMENT (NOT APPROVED)

## Source of truth and permitted scope

Implementation Plan v1.1.1 Phase07, D-03 and Gold Dataset sections require actual model inference on a permitted development/integration host, traceable Recall@K/MRR/nDCG, model dimension, distance, timing and memory plus license review. Group C final organization On-Prem GPU/VRAM/scale tests occur **only in Phase18**. This draft benchmark is Group B isolated development evaluation, not Production.

## Two actual, independently released candidates

- `intfloat/multilingual-e5-small`: pinned HF commit `614241f622f53c4eeff9890bdc4f31cfecc418b3`; MIT license (declared by public model card), 384 dimensions; asymmetric `query: ` and `passage: ` prefixes. Verified public source: https://huggingface.co/intfloat/multilingual-e5-small.
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`: pinned HF commit `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`; Apache-2.0 declared license, 384 dimensions; no E5 prefixes. Verified public source: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2.

License metadata is checked again at runtime; **legal approval is not yet granted**. Model weights must be actual pinned public safetensors on the runner, hashed SHA-256 and loaded locally with `trust_remote_code=False`. No hosted third-party inference API is used. CPU-only CI is legitimate Group B, **not** a final organizational GPU capacity test.

## Protocol and methodological caveats

- 18 authored **synthetic** source snippets; 20 labeled queries (17 with manually authored relevant IDs, 3 intentionally without). Persian colloquial, Arabic, Persian-English mixed, version/outdated concepts, separation of public/internal and domains. The labels are `SYNTHETIC_AUTHOR_UNREVIEWED`, not independently adjudicated Gold Corpus.
- Both models run on the exact same dataset SHA, CPU, cosine normalization, exact brute-force dense retrieval, with scope/domain filters before ranking. E5's required query/passage prefixes are applied. No ANN index, real Qdrant latency, reranker or sparse/hybrid claim is made.
- Real metrics: Recall@1/3/5, MRR@10, nDCG@10, per-category Recall@1; model warmup/reuse, load and document-batch timings, query encoding latency p50/p95/p99, process RSS and weight file SHA/license.
- Queries without ground-truth relevance are EXCLUDED from ranking quality denominator. Zero-evidence abstention cannot be scored from embedding similarity alone, and is explicitly marked **NOT_EVALUATED**. Small synthetic data cannot justify a final D-03 winner or contractual quality threshold.
- GitHub Actions artifacts are the source for actual execution evidence. If either real model download/encoding fails, status is `BLOCKED_OR_FAILED` and no model score may be asserted. The comparison job requires two success artifacts and matching dataset SHA.

## Remaining gates

After both model artifacts are verified, add an independently reviewed domain-specific permitted Gold Set (incl real relevance judgments), repeat N times and evaluate confidence and false positive cases, compare against lexical baseline and actual Qdrant transport, record license and resource review, perform genuine approved D-03 decision including dimension/metric/schema and later versioned reindex. Phase07 durable jobs/publication/revoke A/B remain missing. Corporate GPU verification stays Phase18 (P18-P07-C01..C07).

**Phase07 status remains IN_PROGRESS; Full Technical DoD NOT_SATISFIED; Production NOT_READY.** No prior PR merge, review, production data or Group C test is implied.
