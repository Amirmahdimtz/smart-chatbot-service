# Phase09 — kickoff evidence and gates, 2026-10-27

**Scope:** pure Core offline versioned prompt envelope, source-mapped SHA-256/UUID citation anchors, untrusted document JSON boundary, deterministic no-evidence abstention, strict model-output schema/citation validation. **No actual LLM inference has occurred and none is claimed.**

**Tests A Executed + Actual Results:** pending exact Phase09 PR SHA CI at kickoff.
**Tests B Executed + Actual Results:** **no Phase09 actual LLM/model serving tests executed**; predecessor's real Qdrant/PostgreSQL integration alone is not model/grounding evidence.
**Tests A/B Required but Missing:** P09-B01..B06; actual approved D-02 self-hosted LLM model/runtime and Gold Corpus/metrics, stream/timeouts, per-claim grounding and fresh revoke checks, provenance/license/quality selection and expert technical acceptance.
**Tests C Deferred to Phase18:** P18-P09-C01 through P18-P09-C06, all DEFERRED_TO_PHASE_18 / NOT_RUN / NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P09-C01, C02, C03, C04, C05, C06.
**Technical DoD Status:** NOT_SATISFIED; ENGINEERING_IN_PROGRESS.
**Phase Status Before/After:** NOT_STARTED → IN_PROGRESS.
**Production Release Status:** NOT_READY.

Phase08 has a previous exact-HEAD successful 6/6 CI after independent evidence budgeting, but real model/semantic gates remain open. Opening Phase09 does not change the statuses of Phase05–Phase08 or permit a merge or corporate server test.


## First actual source-code CI, corrections and pending same-head verification

- Initial [CI 40509515391](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40509515391) ran general unit suite **118 PASSED / 31 SKIPPED / 2 warnings** and Ruff static check PASS, but `verify` did **not** pass because two files needed Ruff format. This is a **FAILED** full-workflow attempt, not accepted evidence of all six jobs.
- Source was strengthened to require `normalize_persian(original)==canonical`, exact page-relative span length, and a citation fingerprint additionally bound to original-text SHA-256. The formatter differences have been corrected on code SHA `448c89e501b5301d736ce545833a46c3f8e84da2`.
- [CI 40510020985](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40510020985) for the corrected code has verified five SUCCESS jobs (Docker, PostgreSQL, Qdrant, Secret Scan, Ingestion); `verify` was **IN_PROGRESS** when this entry was authored, stuck in OCR dependency setup. **Do not treat this run as 6/6 success until GitHub reports completed/success.** The inherited Group B service integrations are real, but **NO actual LLM inference** has been performed.

**Tests A Executed + Actual Results:** Initial observed `118 PASS / 31 SKIP` in earlier code CI (whole job failed Ruff); code-corrected full-A conclusion pending.
**Tests B Executed + Actual Results:** Real inherited isolated services executed in successful dedicated jobs; Phase09 LLM-serving B01–B06 NOT_RUN.
**Tests A/B Required but Missing:** Attributable real self-hosted LLM runtime/model benchmark D-02, grounding Gold Set D-12, complete Phase07/08 publication→retrieval authorization and fresh reauthorization, streaming/timeout/cancellation, injection/fake citation real-model negatives, independent acceptance.
**Tests C Deferred to Phase18 / IDs:** P18-P09-C01..C06, NOT_RUN/NOT_PASSED.
**Technical DoD:** INITIAL_OFFLINE_CONTRACTS — MODEL_DEPENDENT_B_GATES_MISSING.
**Phase Status:** IN_PROGRESS → IN_PROGRESS.
**Production Release:** NOT_READY.
