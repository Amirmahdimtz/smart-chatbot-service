# ADR-0013 — Phase09 dependency-safe LLM Answer Engine kickoff

Date: 2026-10-27
Status: PROPOSED / DEVELOPMENT ONLY

## Upstream state and authorization

Owner requested: finish all Phase08 work independently possible, then start Phase09, otherwise finish Phase08. Phase08 independent structural evidence checks were added and verified in CI; actual retrieval/Reranker/quality gates are blocked by unfinished Phase07 and decisions D-03/D-04/D-12. Development on Phase09 begins as stacked Draft on unmerged Phase08. Phase05–Phase08 are **not** reclassified CLOSED and are **not** merged.

Implementation Plan v1.1.1 Phase09 DoD requires a **real self-hosted LLM serving runtime in authorized Development/Integration** and its actual A/B results, independent of corporate final GPU performance which is Group C and deferred to Phase18. Decision D-02 (LLM/quantization/license/model/serving selection) is still open. No third-party cloud LLM, unapproved model or fake acceptance is authorized.

## Implemented first slice

- Versioned `grounded-qa-p09-v1` Prompt template contract, with original document text explicitly serialized as **untrusted data** separate from system policy. This formatting is not a complete prompt-injection defense.
- Immutable citation anchors derived from real supplied document UUID, version, chunk, page and actual raw extraction span; canonical SHA-256 must match input.
- Strict answer JSON parsing and whitelisted structure, duplicate-key, invalid/fabricated Citation ID, empty evidence, over-context and malformed-output rejection.
- No-context deterministic abstention without invoking any model.
- Successful syntax/provenance validation **never equals semantic grounding verification**: the resulting state is `requires_grounding_review` and `grounding_verified=False`. No answer is published/returned automatically from this slice.
- No LLM HTTP client, weight download, model inference, streaming endpoint, chat persistence, untrusted tool execution or credentials are introduced.

## Required later before closure

- Signed D-02 LLM/quantization/serving choice based on actual licensed Persian Gold Set evaluation, model checksum, TTFT/E2E/VRAM and reproducible structured output.
- Genuine self-hosted LLM adapter with concurrency, timeout, cancellation, streaming and health, model lifecycle metadata and actual allowed Group B inference.
- Actual Phase08 PostgreSQL-authorized Retrieval/Reranker evidence and **fresh authorization validation before response release** (including mid-stream revoke/version change).
- Per-claim semantic grounding checks, evidence sufficiency and contradiction/outdated handling, prompt-injection adversarial evaluations, safe tool/action assertions, independent Security/domain review.
- D-07/D-08 and D-12 data/quality rules remain open. Real corporate On-Prem Group C only in Phase18.

**Decision:** Phase09 `IN_PROGRESS`, DoD not satisfied, Production `NOT_READY`. No mock can be counted as actual LLM integration.
