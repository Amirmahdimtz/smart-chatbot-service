# ADR-0012 — Phase08 bounded development without Phase07 acceptance

Date: 2026-10-27
Status: PROPOSED / DEVELOPMENT ONLY

## Context

Owner requested Phase08 development although Phase07 remains IN_PROGRESS (PR#5 Draft on unmerged Phase06 PR#4; Phase05 PR#3 likewise pending). The authorized Group A/B technical exit gate in Implementation Plan v1.1.1 for Phase08 requires **real** approved retrieval/reranker models and a representative Persian Gold Dataset; upstream D-03 (Embedding/Reranker), D-04 (sparse/hybrid strategy), D-07/D-08 (organization policy), D-12 (quality threshold) and Phase07 approval/publish/revoke controls are not delivered. Do not translate CI success on Phase07 synthetic vectors into ready-to-use knowledge search.

## First engineering slice

- Create a stacked Draft Phase08 PR against Phase07, preserving all predecessor states.
- Use Phase06 `normalize_persian` for the **query path** to prevent a second independent normalizer.
- Pure Core RRF candidate fusion contract with configurable `rank_constant`, bounded candidates, stable order and source-identity conflict detection. This is a *fusion primitive*, not a decision on D-04 or an operating hybrid search pipeline.
- Use existing Phase04 QdrantProvider, whose search requires `deployment_scope`, domain, classification, authorized document IDs and `published=True` filters. Reject malformed, foreign-scope, nonfinite-score and contradictory payloads. Do not expose Qdrant scores or payloads as evidence.
- Add an authoritative PostgreSQL read-side Repository which checks `KnowledgeChunk` → `DocumentVersion` → `KnowledgeDocument` → `KnowledgeSource`, requiring matching IDs, owner, domain, zone, active source, synthetic classification/policy and **published version**. Check canonical checksum and original/canonical/source span evidence; omit any invalid/revoked/absent row. A Qdrant `published` payload is not an authorization grant.
- Add a **development/integration-only, synthetic-only, no-controller dense candidate probe** taking caller-provided numeric vectors solely to verify transport and filters. Neither Embedding nor Reranker nor Publication is implemented by this probe. The caller's `allowed_document_ids` are just an early Qdrant filter; PostgreSQL owner filtering remains authoritative.
- Unit and genuine isolated PostgreSQL/Qdrant Group B tests, including forged published points and revocation. Test-only manual PostgreSQL `state=published` transition is a fixture for the READ predicate only and is **NOT** Phase07 publication E2E approval evidence.

## Non-negotiable open gates

- No public retrieval endpoint or LLM answer, no real document/prompt; no source content returned from unapproved Phase07 state.
- Missing actual dense encoder and real ranked corpus, sparse/lexical selection, Reranker model/lifecycle/timeout, mixed Persian Gold Set benchmarks, contradictory/dated evidence, explainable abstention, approved D-03/D-04/D-12 metrics.
- Phase07 requires durable approval/manifest and atomic visible-version publication; current DB `published` predicate alone is insufficient to implement Phase07 publication.
- Organization IdP/Vault and real-data policy remain unapproved and no physical organization testing is performed before Phase18.
- Phase08 remains `IN_PROGRESS`, not `CLOSED`; Production `NOT_READY`.
