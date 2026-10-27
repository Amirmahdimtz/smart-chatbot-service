# Phase07 — Engineering kickoff, index lifecycle design

## Scope and current dependencies

Reference: SCB Implementation Plan v1.1.1, Architecture Guide, ADR-0011. Phase07 is a development branch stacked on Phase06 (PR#4), not a technical acceptance/merge of either predecessor.

Planned full lifecycle: source validation → durable index intent/manifest in PostgreSQL → **real selected** model batch encoder with warm reuse → Qdrant isolated versioned collection staging → vector/payload checksum/readback → attributable document approval → PostgreSQL visibility/version switch with authorization fence → revoke-first filtering → async garbage collection → reindex/rollback.

**This first implementation slice covers only:** validated immutable manifest in Core, embedding output contract, synthetic-only unpublished Qdrant stage using existing Infrastructure QdrantProvider, regression of prerequisite multi-page source spans, and actual Qdrant transport test. No approved embedding model, live Indexing Job, final publication, model benchmark, alias cutover or retrieval API exists yet in Phase07 code.

## Index manifest

The deterministic UUIDv5 and SHA-256 digest cover document/version scope, domain, synthetic classification, model ID and revision, dimension, distance, schema, processor/normalizer versions, sorted chunk IDs/ordinals, canonical checksums and source page/span offsets. Invalid input fails before any Qdrant operation. Parent canonical byte text is not stored in the manifest, but its checksum is validated.

The existing Phase04 Qdrant collection indexes remain scoped by deployment/domain/classification/document and `published`. Phase07 currently stages `published=False` only. Point IDs presently depend on (chunk_id, document_version_id, schema_version). This is not enough to isolate two model revisions that share schema version; a future migration must enforce model-revision/schema collection isolation before any publish/reindex. Alias switching before an index is complete is expressly forbidden.

## Model selection and quality acceptance

D-03: evaluate **at least two actual legal/offline-deployable Persian and mixed-language embedding candidates** on the same annotated synthetic/authorized Gold Dataset. Record model binary/checksum/revision/license and runtime configuration, Recall@k/MRR, inference latency p50/p95, cold/warm memory/VRAM, dimension/metric and tokenizer/normalization. No names, winners, measurements or runtime validations are asserted before measurement.

D-04: similarly evaluate candidate sparse/lexical representations and the dense-only baseline before choosing final hybrid. If sparse is not available, final hybrid remains blocked. Final hardware/model approval and organizational capacity remain Phase18 C.

## Publication safety and next iteration

Never trust a Qdrant `published` flag alone as authorization: query reauthorization must consult PostgreSQL source/document version status, scope, role and consent. A publication coordinator will require finalized source evidence, real approval and a durable versioned manifest. Revoke must deny immediately in the authority (PostgreSQL) even when Qdrant is delayed. Per-document visibility is a DB decision rather than raw alias mutation.

Next required engineering steps: durable manifest and Job table+Alembic migration; restart/lease fencing; selected real embedding runtime and benchmark; consistent index readback and drift repair; fenced publish/revoke races and atomic visible version; rollback/rebuild tests. Real Group B integration must follow each implementation, no skipped test counted passed.
