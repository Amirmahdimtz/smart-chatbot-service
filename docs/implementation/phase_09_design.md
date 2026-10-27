# Phase09 — LLM Inference, Prompt, Citation & Abstention (initial slice)

Reference: Implementation Plan v1.1.1 Phase09, Architecture Guide, ADR-0013.

## Data flow and security boundaries

`Fresh AuthorizedEvidence from PG source/version policy → context selection and exact raw source spans → versioned prompt envelope with untrusted source JSON → future genuine D-02 self-hosted LLM → strict structural output validation → future per-claim grounding/fresh auth and citation reconciliation → approved response or abstention`.

This first slice implements **only** a pure Core evidence/prompt and structural answer-validation contract. No Core imports Infrastructure; there is no inference, public API, tool execution or content persistence. An untrusted document may contain fake system messages; its contents remain a serialized JSON text field and never a backend tool directive. These boundaries are necessary but cannot guarantee resistance to all prompt-injection attempts.

## Citation contract

Each citation ID is UUIDv5 over template_version + document ID + chunk ID + PDF page/nullable page + page-relative original-text span + canonical SHA-256, namespaced by the actual DocumentVersion UUID. The source is rejected if canonical hash, types, offsets or context limits are inconsistent. The checksum proves consistency of supplied bytes, not that they originated in authorized PostgreSQL; only an upstream fresh PG check can prove that. A stale/revoked version must be rechecked **again before response release** in a future orchestration component.

Prompt `system_message` explicitly denies document instructions, disclosure of policy/tool authority and fake external actions. `user_message` is stable JSON with controlled query normalization, domain, audience role and bounded evidence excerpts. Role/domain values are syntax-validated; true user authorization must come from the upstream Security principal, not from these strings.

Answer JSON exact keys: `answer`, `citation_ids`, `abstain`. Unknown keys, duplicate keys, malformed JSON, empty answer without abstention, references to unknown or duplicated citation IDs, forged inline citation markers, output above budget, and inconsistent abstention fail closed. With no sources the caller must use `abstain_without_evidence` and must not invoke a model.

## Truthful release policy

A structurally valid nonabstained output has **status `requires_grounding_review`, grounding_verified=False**. It must not be presented as factually supported because structural Citation matching does not check claim-to-source entailment, PII, tool assertions, sensitive content or stale-source race. Real LLM grounding evaluation and authorization gate remain mandatory.

## Remaining Phase09 gates

D-02 LLM/quantization/license/cpu-gpu model Benchmark; actual self-hosted inference provider and lifecycle with streaming/timeout/cancel/health; D-12 generation/citation/abstention Gold Dataset, per-claim policy and false grounded answer metrics, prompt injection/contradiction/dated/invalid source tests; true Phase07 published and Phase08 authorized results and independent accountable review. Group C `P18-P09-C01..C06` is Phase18 only, unexecuted.
