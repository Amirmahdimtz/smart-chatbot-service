# Phase07 — Actual candidate Embedding → PostgreSQL → Qdrant evidence

Date: 2026-10-28
PR: https://github.com/Amirmahdimtz/smart-chatbot-service/pull/11 (Draft stacked on PR #10 and #5; NOT MERGED)
**Scope:** Synthetic-only, internal-zone Development and disposable Integration. Candidate model use is NOT final D-03 selection. **No HTTP publication, no approved production domain corpus.**

## Actual implementation

- Pinned real CPU model runtime: `src/infrastructure/providers/embedding/candidate_cpu_embedding_provider.py`; E5 and multilingual MiniLM revisions fixed, warmup/reuse, bounded 32-text request and 8-text inference batch, semaphore of 1, CPU only, no cloud model API.
- `PostgresIndexSourceRepository` independently retrieves actual PostgreSQL Chunk/Version/Document/Source rows with exact owner/domain/scope/classification/active-source and `awaiting_approval` predicates; checksum and source-span checks. This fixture was created directly in an isolated CI transaction, NOT via the genuine Phase05 ingestion approval API.
- `SyntheticCandidateIndexCoordinator` builds model-versioned immutable Manifest from PG data, encodes with pinned real model, checks vector count/dimension and finiteness, reads PG again before staging, writes via actual authenticated Qdrant `published=False` and reads PG again afterward; no alias/publish operation.
- Genuine Qdrant readback shows 384-float vectors and `published=False`; `published=True`-filtered retrieval yields no candidate. Repeated same version produces same point IDs and reuses one model instance. Wrong principal/domain and revoked version are denied by real PostgreSQL.
- The experimental coordinator does NOT persist indexing job state or manifest to PostgreSQL; no durable retry state, atomic publication, revoke rollback, version visibility or full Phase07 lifecycle is claimed.

## Source-specific CI and actual results

**Tested implementation SHA:** `5e170fa2e5d78daaf6751477ee6c4d45bffdfa26`.
**GitHub Actions:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40658660406.

- **Tests A Executed + Actual Results:** Python general suite **107 PASSED / 30 SKIPPED / 2 warnings**; Ruff Check+Format PASS and strict pip-audit `No known vulnerabilities found`, Docker/Secret Scan PASS. SKIP is not PASS.
- **Tests B Executed + Actual Results:** Real disposable PostgreSQL+authenticated Qdrant+true CPU safetensors inference **1 PASS for E5-small** and **1 PASS for multilingual MiniLM-L12-v2**, in separate CI model jobs; each ran the actual indexing E2E and model seed benchmark. Prior isolated PostgreSQL and Qdrant integration jobs PASS. Ingestion/recovery overall CI conclusion must be checked separately before claiming whole run 8/8 SUCCESS.
- **Historical failed attempts:** initial PR11 run 40657696793 had genuine model integration success but `verify` failed import sorting; later CI attempts exposed four Ruff formatter differences and a final Qdrant assertion formatter difference. These were corrected by code SHA above. All failed attempts remain failed, never counted PASS.
- **Model benchmarking:** E5 and MiniLM previously both actually inferenced on identical 18-source/20-query synthetic seed, Recall@1=0.941176, Recall@5=1.0, MRR@10=0.970588 and nDCG@10=0.978290 on only 17 positive relevance questions; real latest source job has both weights SHA256 consistent with prior pinned revisions. Model selection D-03 stays OPEN.
- **Gold review:** `benchmarks/phase07/review_packet_v0.1.json` exports 20 proposed synthetic rows, but contains author-supplied relevance proposals, so it is **NOT** a blinded double-annotated Gold Dataset. Its reviewer_A, reviewer_B, adjudicator, data owner and security approvals are ALL empty. **Do not distribute this version directly as blinded reviewer material**; suppress proposed labels from a separate reviewer export before independent annotation. `phase_07_gold_review_protocol.md` documents independent review and adjudication. No human approval has been obtained.

## Unfinished / phase report

**Tests A/B Required but Missing:** Full approved expert Gold Set and double-blind independent relevance agreement, D-03 model/legal signoff, D-04 sparse/hybrid decision, durable PostgreSQL index job+manifest state, genuine Phase05-to-07 authorized indexing queue, atomic visible-version publish, immediate revoke, race-tested rollback/reindex and expert technical/security reviews. These are necessary for Phase07 technical closure; no mock substitutes for actual core integration.

**Tests C Deferred to Phase18:** `P18-P07-C01..C07` all `DEFERRED_TO_PHASE_18`, NOT_RUN, NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P07-C01, C02, C03, C04, C05, C06, C07.
**Technical DoD Status:** `REAL_CPU_PG_QDRANT_HIDDEN_STAGING_A_B_VERIFIED — FULL_PHASE07_DOD_NOT_SATISFIED`.
**Phase Status Before/After:** `IN_PROGRESS → IN_PROGRESS`.
**Production Release Status:** `NOT_READY`.

Corporate On-Prem GPU/IdP/network/HA/capacity verification is Group C in Phase18 only. No corporate server testing requested.
