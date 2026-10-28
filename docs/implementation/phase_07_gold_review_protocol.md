# Phase07 Gold Dataset review & adjudication protocol v0.2

**State: CANDIDATE_ONLY / EXPERT_REVIEW_NOT_DONE — not a certified Gold Dataset.**
**Date:** 2026-10-28. Scope: authorized synthetic/public domain content only, no corporate documents or organization network.

## 1. Source of ground truth

The existing `benchmarks/phase07/gold_synthetic_v0.1.json` is an *author-authored synthetic seed*, with 18 passages, 20 queries, 17 manually proposed relevant answers and three zero-relevant/abstention probes. It must not be relabeled Gold or treated as real enterprise distribution. Its explicit scope/domain filters are a security benchmark control, not evidence of a real IdP/ABAC policy.

## 2. Independent labeling roles (unassigned)

For each question, recruit **two independent domain reviewers**, using versioned snapshot of authorized original excerpts, citation/section/page and a pre-agreed policy-owner approval. Roles only: `domain_reviewer_A`, `domain_reviewer_B`, `adjudicator`, `data_owner`, `security_reviewer`. No approvals or identities are invented here.

## 3. Required record for each reviewed query

`query_id`, `query_text_sha256`, `domain`, `authorized_scope`, `document_snapshot_sha256`, `corpus_license_or_permission`, `reviewer_A_id`, `reviewer_A_timestamp`, `reviewer_A_relevance`, `reviewer_B_id`, `reviewer_B_timestamp`, `reviewer_B_relevance`, `agreement`, `adjudicator_id` (if disagreement), `adjudication_timestamp`, `final_relevance`, `rationale`, `evidence_page`, `source_start`, `source_end`, `negative_or_abstain_reason`, `data_owner_approval_ref`, `security_approval_ref`. Reviewers must not see the scores/rank order or labels produced by candidate models. Neither auto-generated scores nor a ChatGPT assertion constitute independent adjudication.

## 4. Dataset composition gate

Include common/rare Persian spellings, ZWNJ and digit variants, colloquial/standard questions, Arabic with diacritics, religious citations with exact provenance, Arabic/Farsi mixed texts, Persian/English terminology, contradictory and deprecated versions, no-answer/abstain queries, duplicated near-matches, adversarial prompt-like text as *untrusted document data*, and explicit cross-domain/cross-zone negatives. Distinguish **query-level scope** from **documents the principal is authorized to read**. Make sure zero-label queries are evaluated with a separate abstention policy/threshold, never silently included in Recall denominators.

## 5. Minimum release evidence / no fake threshold

Before a versioned `gold-v1` can be declared, obtain (a) checksum-fixed candidate source snapshot; (b) two independent blinded labeling sheets; (c) conflict adjudication and justification; (d) dataset/policy owner written approval; (e) license/usage permission; (f) completed domain/security review; (g) Query-to-evidence offset validation and separate holdout partition; (h) agreed D-12 quality thresholds. Do **not** invent numerical thresholds or mark any unsigned row accepted. Re-evaluate both pinned D-03 models, sparse baseline and reranker on the approved Gold, reporting Recall@K, MRR, nDCG, confidence intervals, abstention/false positives, p50/p95 and resource footprints. Fix both model and dataset hashes in the final ADR.

## 6. Next technical work

The approved Gold set does not yet exist. The first real Integration slice may exercise *pinned candidate weights* on synthetic data, read only from authorized PostgreSQL, and stage to Qdrant `published=false`. This is a legitimate bounded Group B experiment, **not** approval for D-03 or a Phase07 publication transition. Group C On-Prem tests stay exclusively Phase18.
