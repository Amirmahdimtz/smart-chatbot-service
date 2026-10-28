# ADR-0015 — Durable Indexing and PostgreSQL-authoritative publication (Phase07)

Date: 2026-10-28
Status: PROPOSED / SYNTHETIC DEVELOPMENT A/B ONLY — NOT APPROVED FOR ORGANIZATION

## Decision and transactional limitations

PostgreSQL is the **sole authorization/visibility authority**. A Qdrant payload `published=True`, an alias, and a model output can only produce *candidate IDs*; they do not grant read access. Every result, span and citation MUST be re-authorized against the current active PostgreSQL source, `DocumentVersion.state='published'`, ownership, domain, classification and version, and (for this new schema) the authoritative `IndexPublication.active_version_id`. The last pointer check is a requirement for future retrieval integration; Phase08's earlier read-side filter checks state but does **not yet** check this pointer.

A distributed atomic transaction across PostgreSQL and Qdrant is unavailable. The safe sequence is Qdrant staging `published=False` → verify exact immutable manifest points → explicit synthetic reviewer approval → Qdrant alias/flag prepare → one PG transaction updating active-version pointer, previous version to `superseded`, current version to `published`, and job status. A failure in PG triggers a best-effort Qdrant hide; even if that hide fails, PostgreSQL continues to deny the new version. Changing an active version within PG is atomic; it is **not** claimed that Qdrant payload update and PostgreSQL commit are atomically coordinated. Qdrant filters reduce candidate exposure but cannot replace the PG final gate.

For revoke: commit PostgreSQL `revoked` + active pointer removal FIRST; index job `cleanup_pending=True` acts as a durable outbox. Qdrant cleanup may run later or after an outage and is idempotent. Existing published Qdrant vectors may persist temporarily but must not become authorized by a stale cache or citation. Full end-to-end Phase08 retrieval gate integration and race/TOCTOU audits remain a blocker to true acceptance.

## Schema / fencing

Alembic revision `0004_index_lifecycle` adds `index_job` (unique document-version/scope, manifest checksum/model/revision/dimension/count, 3 attempts, token + UTC lease, state and cleanup_pending), `index_manifest` (immutable versioned manifest JSON, SHA, full Qdrant point ID receipt), and `index_publication` (one active version per document, monotonic generation). `IndexJobRepository` uses PostgreSQL transactions and row locks to gate idempotent enqueue, fenced claim, complete/fail/retry, synthetic reviewer approval, PG cutover and PG-first revoke. A stale/expired lease or changed manifest cannot complete a job. Repeat upserts are deterministic; partial Qdrant failures remain unpublished and the leased job may retry. Actual isolated Integration tests exercise the schema, real models and authenticated Qdrant.

## Deliberate restrictions

- **No organizational IdP approval exists in this PR.** `approve_synthetic_async` accepts a separately named synthetic CI actor under `development/integration`, `internal`, `synthetic_only` configuration only; it is not a real policy/segregation-of-duties proof.
- No public/controller endpoint added. Real corporate documents, Production credentials, public publication, GPU hardware and organizational networks are prohibited.
- The existing 18-passage/20-query authored synthetic corpus remains unreviewed. `export_blinded_review.py` strips all author-proposed relevance IDs and produces a separate **candidate** packet for independent reviewers. Neither dual review, adjudication nor data-owner/security signatures have been obtained. Do not claim D-03 / D-12 acceptance.
- The tested scope does not yet include a full real two-version model-change reindex and alias rollback/recovery campaign, approved corpus data, all partial failure/race variants, or full Phase08 cited-answer integration. These remain required A/B work.
- Group C On-Prem GPU, IdP/Vault, HA/DR, network isolation, load and security acceptance remains only Phase18 under `P18-P07-C01..C07`, NOT_RUN / DEFERRED_TO_PHASE_18.

## Status

Phase07 `IN_PROGRESS`; full Technical DoD `NOT_SATISFIED`; Production `NOT_READY`. This ADR is a proposal, not expert approval. No previous phase or PR status is changed by this document.
