# Evaluation, Acceptance and Gold Dataset Contract

**Status:** Specification only, no collected or labeled corpus and no benchmark execution.

## Dataset specification

For each domain `UC-REL`, `UC-HR-1`, `UC-HR-2`, `UC-HR-3`, `UC-RES`, `UC-DEV`, `UC-TASK`, collect signed-off, access-controlled examples with: `query`, `domain`, `authorized_scope`, `source_version`, `relevant_evidence`, `acceptable_answer`, `should_abstain`, `citation_expectation`, `approval_expectation`, `reviewer`, `dataset_version`, `classification`. Include Persian formal/colloquial, Arabic/Persian mixed text, contradictory sources, revoked versions, no-evidence, injection, sensitive/unauthorized and concurrent-change examples. Sensitive data may only enter approved test infrastructure.

## Metrics and criteria

| Layer | Required measurement |
|---|---|
| Retrieval | Recall@K, MRR, nDCG, ACL-filter correctness, fresh/revoked index behavior |
| Reranking | Before/after nDCG and latency/VRAM |
| Answer | Faithfulness, citation precision/coverage, abstention, contradiction handling |
| Workflow | Hard eligibility, consent, approval enforcement, idempotency and human reviewer acceptance |
| Security | 0 unauthorized Public/Internal, HR or cross-owner data disclosures in acceptance suite |
| Operations | TTFT and end-to-end P50/P95/P99, tokens/s, queue lag, timeouts, error rates |
| Recovery | RPO/RTO evidence, restored citation/state consistency, failover behavior |

Thresholds and signed SLOs remain `D-12`; no pass percentages, model selection, throughput or target claim is currently verified. Store corpus versions, reviewer initials/role (not PII in public Git), model/prompt/index/config hash, hardware profile, test environment, raw measurements, negative test counts and approvals with each report.

## Test gates

Phase 01: validate requirement traceability, seven scenario mappings and policy identifiers. Phases 06–09: gold extraction/retrieval/generation and citation accuracy with real self-hosted components. Phases 12–14,16–17: domain owner approval and negative access/workflow tests. Phase 18: full E2E, adverse input, isolation, load/soak, HA and real restore. A test which cannot run without systems or signed data is **PENDING**, not PASS.
