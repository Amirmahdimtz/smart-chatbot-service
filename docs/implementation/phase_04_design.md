# Phase 04 — Qdrant Technical Design (synthetic-only)

Date: 2026-10-24. Owner instruction: commence Phase 04. Baseline: main `0b34f457bacfe4aba704ff01563fcd1c4e62a97c`.
Entry gate: ADR-0007 `CONDITIONAL_GO_FOR_DEVELOPMENT_ONLY`; Phase 03 technical `CLOSED`. Earlier Phase 01/02 are still `IMPLEMENTED_AWAITING_VERIFICATION`.

## Scope and source-of-truth boundaries

- Four-layer structure preserved; `QdrantProvider` is an Infrastructure `@inject` singleton with `ConfigReader` and existing Vault injected. FastAPI lifespan starts/closes it only if opted in. No controller, RAG, inference, ingestion worker, new PostgreSQL table or Alembic migration.
- PostgreSQL / trusted Policy retains the authoritative publication and authorization state. Qdrant `published` is a candidate pre-filter, **not** permission to present results. The downstream authorized Core workflow must re-check every returned point against PostgreSQL after query and before sending to an end user. Phase 04 intentionally exposes no Qdrant HTTP search API.
- Public/Internal use distinct deployment credentials and endpoints plus physically isolated deployments in the final topology. Every local name includes the fixed configured zone, and every query filters deployment scope and explicit authorized document IDs, domain and classifications. No unscoped query is exposed. Config zone mismatch fails before network access.
- No real HR/PII/organization data, production Qdrant provisioning or public access is approved. The current synthetic `published=True` fixture is **only test metadata** and makes no assertion of an approved publication policy.

## Pinned technology and compatibility

- Python SDK: `qdrant-client==1.20.0` (async REST `AsyncQdrantClient`). Isolated CI Qdrant server: `qdrant/qdrant:v1.20.0`. Both are officially released 2026-10-22; pair is exercised with authentic network/API-key requests. Docs: https://github.com/qdrant/qdrant/releases/tag/v1.20.0 and https://github.com/qdrant/qdrant-client/releases/tag/v1.20.0 .
- HTTPS required outside development/integration. Credentials from deployment environment or the existing asynchronous Vault KV-v2 abstraction; no direct organization secret is committed. Integration permits loopback HTTP with disposable service credential only.
- Timeout configurable (default 5s) and bounded retry (default two retries) only for network errors, timeouts, 429 and 5xx. Authentication/validation/4xx errors fail immediately, with credential-free error text. No retries on partial batch validation failures.
- SDK API usage: `create_collection`, `create_payload_index`, `get_collection`, `get_aliases`, `update_collection_aliases`, `upsert(wait=True)`, `query_points`, `delete(wait=True)`, `create_snapshot`. Compatibility beyond the pinned tested pair is not inferred.

## Collection and payload contract

Config: `SCB_QDRANT_COLLECTION_PREFIX` (default `scb_vectors`), `SCB_QDRANT_SCHEMA_VERSION`, `SCB_QDRANT_DIMENSION` (required only if enabled), `SCB_QDRANT_DISTANCE` in Cosine/Dot/Euclid. No embedding model or final dimension is selected by Phase 04 (D-03/D-04 remain open).

- Physical collection: `{prefix}_{zone}_v{schema_version}`.
- Active read alias: `{prefix}_{zone}_active`. Explicit alias cutover is atomic via Qdrant API; no destructive in-place dimension migration. Rollback is explicit cutover to the compatible previous version while previous collection exists.
- Deterministic UUIDv5 point identity includes `chunk_id`, `document_version_id`, `schema_version`. The document ID is enforced as payload metadata; identity stability for the same chunk/version/collection avoids accidental duplicate creation on retry.
- Payload: `chunk_id, document_id, document_version_id, domain, deployment_scope, classification, published, index_version`; no canonical chunk text or unapproved HR attributes. Required keyword/bool indexes: `deployment_scope, document_id, domain, classification, published`. These metadata fields are not a substitute for authoritative Policy checks.
- Bounded batch upsert rejects duplicate deterministic IDs, invalid domain/classification, nonfinite/wrong-dimensional vectors, missing UUIDs, invalid publication type and batch size overflow. Delete is constrained by document ID, zone and domain. Low-level provider operations are for trusted backend code only.
- Search is explicitly scoped by configured zone, domain, non-empty authorized classification set, non-empty UUID document ID allowlist and `published=True`; no HTTP endpoint, client-originating authorization or broad read is introduced.

## Recovery, migration and operations

1. Export PostgreSQL source/index manifest and checksum metadata once Phase 07 owns them. Keep collection schema/alias metadata, SDK/server versions and Qdrant snapshots together. Avoid snapshots of unapproved/sensitive data.
2. In disposable development Qdrant, create new versioned collection, construct indexes, re-upsert synthetic records, verify filter/search/count and atomically switch alias. Preserve old collection until the new version is accepted. A rollback switches the alias back without deleting the current collection. No implicit collection deletion.
3. Snapshot creation uses the supported collection endpoint; true restore of production multi-node, alias metadata, network and HA/DR is **Group C Phase 18**, not implied by a successful synthetic rebuild.
4. Availability/readiness: a failed opted-in Qdrant startup aborts API startup, and graceful shutdown closes the single client. No client created for each request.

## Open decisions and risks

- D-03/D-04: final embedding dimensions/distance/sparse fusion need Phase 07/08 benchmark and approval.
- D-07/D-08: trusted subject/classification, publication, retention and HR/PII policy remain unapproved. Do not attach real records or enable knowledge APIs.
- Qdrant payload filtering prevents accidental wrong-zone candidates **inside this provider**, but does not provide physical zone separation or complete authorization. Those require runtime network/credentials and Phase 18 acceptance.
- Shared/organization endpoint modifications are prohibited; all integration tests target disposable loopback instances.
- Model-based similarity quality, Hybrid Search, RAG, external Agent, ingestion and LLM are outside Phase 04.
