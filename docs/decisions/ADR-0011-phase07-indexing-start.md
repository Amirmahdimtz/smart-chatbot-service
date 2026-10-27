# ADR-0011 — Phase07 bounded development and model-selection gate

- Date: 2026-10-27
- Status: PROPOSED / IMPLEMENTATION_START_ONLY
- Authorization: owner's explicit instruction to begin Phase07
- Predecessors: Phase05 Draft PR#3 (unmerged), Phase06 Draft PR#4 (unmerged and pending verification)
- This ADR is not a model approval, independent review, Production approval, or phase closure.

## Context and nonnegotiable controls

Implementation Plan v1.1.1 requires at least two real Persian/mixed embedding candidates benchmarked for Recall/latency/resources/licenses, a selected versioned model with D-03 evidence, sparse/hybrid D-04 disposition, durable indexing manifests/jobs, actual partial-outage tests and atomic publish/revoke gates. Group C final On-Prem model and release verification occurs only in Phase18.

The existing Phase04 QdrantProvider already implements authenticated async collections, idempotent upsert, dense schema, alias operations and payload filtering. It is **not** an authorization or publication authority. Phase06 has a known page-offset carryover defect (raw-span state not reset across pages); Phase07's dependent development branch includes a targeted correction and test, but Phase06's own branch and acceptance state remain unchanged.

## Decision for the first engineering slice

1. Stack a Phase07 Draft branch on Phase06; no main/Phase05/Phase06 merge or status changes.
2. Implement deterministic **pre-publication** IndexManifest checksums covering chunk identities, source offsets, parser/normalizer versions, model revision, schema and dimension. Reject inconsistent inputs and nonfinite/incorrect-dimension/zero-cosine embeddings.
3. Reuse existing QdrantProvider in a strictly development/integration, synthetic-only Stage Service. Upsert in bounded batches with `published=False`; there is no alias cutover, publish/revoke or retrieval endpoint in this slice. Real Qdrant integration uses intentionally synthetic numeric vectors **only for index transport testing**, not claimed model evidence.
4. Explicitly block D-03 final embedding model/dimension and D-04 sparse/hybrid selection until two-or-more actual eligible model benchmarks and required decisions exist. No model weights, benchmark scores or approvals will be invented. No mock Embedding Provider will masquerade as production.
5. Future publication must use durable PostgreSQL state, attributable approval, fencing/authorization, manifest consistency/readback, atomic visible-version cutover and revoke-first policy. Qdrant alias alone is NOT a per-document atomic publication guarantee. Phase07 full DoD remains open.
6. A model/chunker schema change must use a separate versioned Qdrant collection with safe index rebuild and rollback. Existing Phase04 point IDs include chunk/version/schema but not model revision: stage must not overwrite an already published collection during reindex; model-revision isolation remains a documented implementation blocker.

## Risks and dependencies

- Phase06 multi-page correction is present only in dependent Phase07 branch; backport/reconcile through separately reviewed Phase06 change before independent Phase06 acceptance.
- Phase05 independent Architecture/Security acceptance and synthetic OCI risk disposition remain pending.
- D-03/D-04 real model selection and sparse strategy are open; no model runtime is assumed available.
- D-07/D-08 organizational permissions and real data are not authorized.
- Full index manifest DB persistence, job leases, batch recovery, publication authorization and version-switching are **NOT implemented in this first slice**.
- Phase18 C IDs P18-P07-C01..C07 are deferred, not passed.

**Phase07 status: IN_PROGRESS. Production: NOT_READY.**
