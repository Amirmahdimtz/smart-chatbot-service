# Phase08 — Hybrid Retrieval, Authorization and Reranking (initial slice)

Reference: Implementation Plan v1.1.1 Phase08, architecture guide, ADR-0012. Stacked Phase08 development does **not** bypass unfinished Phase07 and predecessor independent technical gates.

## Full design / dependency map

1. Authentication and explicit domain/purpose from validated JWT. For currently permitted **synthetic development-only** data, the owner principal is the only supported policy; no organization-wide sharing/RBAC is invented.
2. Phase06 query-only normalizer; eventual selected D-03 real query embedding runtime.
3. Dense and approved D-04 lexical/sparse source retrieval, indexed payload filters and bounded configurable RRF.
4. Mandatory fresh PostgreSQL authoritative source/version/chunk re-authorization against current owner/domain/scope/active source/published version and content checksum. Cross-domain/owner, wrong version, revoked, superseded, disabled or corrupt evidence denied.
5. Reranker as actually selected and loaded in reusable bounded batch runtime, with context budget, stable tie-breaking, duplicate-page span semantics.
6. Evidence sufficiency / contradictions / stale dates / abstention hints; emit source page/raw span only from authoritative PostgreSQL. Prompt assembly and answer citations belong to Phase09.
7. Real integrated dense/lexical/hybrid/reranker benchmark with model revision and trace, measured Gold Set Recall/nDCG/MRR. Final On-Prem hardware performance belongs to Phase18.

## Implemented in this slice (strictly limited)

- `retrieval_contract.py`: reuse normalization, deterministic RRF over pre-ranked dense/lexical candidates, reject duplicate or contradictory IDs and invalid scores. No lexical candidate provider is running.
- `RetrievalEvidenceRepository`: bounded SQLAlchemy multi-table owner/domain/version/active-source and checksum/source-span enforcement. Repository never treats Qdrant as policy authority.
- `RetrievalQueryService.retrieve_synthetic_dense_async`: *no HTTP route*, only synthetic Development/Integration and internal zone, caller-provided test numeric vectors; Qdrant scope filters and payload contract, then authoritative PG recheck. This is **not** query encoding or deployed retrieval; malformed payloads fail closed.
- Automated synthetic unit, actual disposable PostgreSQL and Qdrant probes. Manual fixture manipulation of `published` in isolated B does not represent an approved publication workflow.

## Security nuance

The current PostgreSQL version state is an authoritative **read-side check** but no Phase07 manifest-verified publication transition exists yet. Production use is prohibited. We also do not interpret the `document_ids` parameter as an ACL grant; it is an index prefilter and MUST be supplemented by PG authorization. A failure in Qdrant or PostgreSQL yields no usable evidence. No model scores or magic threshold are asserted.

## Next required work before DoD

Close Phase07 publication/gating and D-03, D-04; add real selected embedding encoder, real reranker with warm lifecycle/timeout, actual lexical candidate provider, explainable sufficiency/abstention, Gold Dataset and threshold decisions D-12, integrated PG+Qdrant+Reranker real E2E, cross-domain denial and timing/expiry tests, attributable technical acceptance. No Group C server requests before Phase18.
