# Phase 05 — Knowledge Source, Secure Upload and Durable Ingestion

Date: 2026-10-24. Baseline: `main` `0c817b1886b1668576e2037394f4b2d5cbf4997b`. Phase entry: ADR-0008, owner-authorized development only. Status: **IN_PROGRESS**; no production permission.

## Reviewed contracts and scope
- Reuse existing `KnowledgeSource`, `KnowledgeDocument`, `DocumentVersion`, `PsqlDbContext`, scoped DI and JWT Principal. Preserve existing six-table foundation and extend it with a versioned, additive Alembic revision and `ingestion_job` / minimal audit records.
- The authoritative data state is PostgreSQL; Qdrant remains untouched. Public/Internal are separate deployments with explicit scope, not a column-only isolation promise.
- Only **synthetic and disposable** data, dev/integration opt-in, internal test-zone route, authenticated synthetic Principal with explicit permission and owner matching. D-07/D-08 are **BLOCKED_DECISION** for any organizational upload, retention, identity binding or publication.
- Scope excludes OCR, extraction, chunking, Qdrant writes, publish/revoke API, LLM, RAG and Agent.

## State, ownership and transactions
- Source: existing id/owner/domain/zone with explicit type and `active/disabled` lifecycle. Document: source-owned record; Version: immutable content bytes/checksum/object key/metadata. No replacement of accepted version content. A new version requires an explicit future workflow, not an in-place mutation.
- Document Version content states: `draft → processing → awaiting_approval`, `draft/processing → failed`; `published/revoked/superseded` are reserved but cannot be entered by Phase 05 code.
- Job orchestration states: `staging → queued → leased → completed`; transient failure: `leased → retry_wait → leased`; terminal `dead/cancelled`. Leases use a per-claim unique token and a server-side expiration; a stale worker cannot acknowledge after lost ownership. `queued/retry_wait/expired leased` are claimed using PostgreSQL `FOR UPDATE SKIP LOCKED`.
- Idempotency: unique `(source, deployment_scope, owner, idempotency_key)`; same key and checksum returns original Job; changed payload is rejected. Within a source, exact checksum reuse returns prior durable content version where allowed; no cross-owner/scope dedup. Concurrency serialized by a locked Source row, not a process-global mutex.
- Persistence occurs before external storage upload: commit a `staging` job and object key, upload to `quarantine/{zone}/{opaque uuid}`, then mark `queued` only after put + integrity HEAD. Worker never claims incomplete staging. A stale staging job is terminally failed and its object quarantined for operator reconciliation; retry with the same key is safe only through an explicit documented policy (no silent second write).
- All state transitions/audit events are transaction-bound; network I/O is never performed while holding a DB row lock. A crash after put and before acknowledgement creates a **durably discoverable** staging record, never an invisible, published object. Failed or abandoned storage is not treated as approved; garbage collection requires reviewed retention policy.
- Quarantine is the only bucket/prefix Phase 05 can write. No public ACLs, presigned downloads, public object references or Qdrant indexes. Scanning failure/timeout returns retriable error **without** changing to approval-ready.

## Provider and lifecycle choices
- S3-compatible object storage using pinned `boto3` and explicit endpoint/credentials; only loopback plaintext in development/integration; TLS required otherwise. Storage bucket should have denied public ACLs, bucket policy, encryption/retention controls owned by deployer. CI candidate: historical `quay.io/minio/minio` image; image support/supply-chain risk requires review, not a permanent vendor decision.
- ClamAV `clamd` `INSTREAM` with bounded chunks, short socket deadline and response parsing. Only a literal clean result is approval-ready; FOUND is terminally rejected, unknown/timeout/unavailable is fail-closed. Do not log file bytes or daemon payload.
- Independent process `python -m src.host.ingestion_worker` composes existing DI, owns DB/storage/scanner startup/shutdown and bounded polling. Not FastAPI BackgroundTasks or in-memory queue.
- Multipart max-body is bounded at the ASGI edge; content additionally read in bounded chunks. Allowed Phase 05 formats should be *narrow* (validated UTF-8 text and structurally parsed digital PDF); ZIP/DOCX, archives, encrypted/invalid/oversized PDFs are rejected rather than decompressed. No OCR or extraction.
- Configuration is opt-in and fail-closed in `ConfigReader`; env/Vault credentials never committed. Change database revision-check atomically with migration and adjust baseline tests for the additive models/providers.

## Recovery and authorization
- Claim expiry/retry exhaustion must produce observable jobs with redacted error codes; heartbeat, cancellation and terminal transitions are compare-and-set by lease token; graceful stop stops polling and releases/lets expire lease.
- Identical retry of job processing is allowed but must never publish or mutate Qdrant. Check checksum while fetching quarantined object and before scan. Durable DB status survives request cancellation and worker restart.
- Controller uses existing auto-discovery and `SecurityService.authorize` with a dedicated permission; request Principal is resolved only from verified JWT middleware. Zone + owner checks occur again in Core/Repository. Validation errors expose codes only; audit excludes object bytes and secrets.
- Real-data access and publication stay disabled until separately signed D-07/D-08 and owning later-phase authorization. A/B tests use synthetic principals and a disposable network topology.

## Required verification
Group A: Ruff, imports/DI, config negative tests, size/signature/malformed PDF/multipart/filename/traversal/ZIP deny, authorization/isolation, state/idempotency/retry tests, OpenAPI contract, strict pip-audit, SBOM, secret scan, Docker build, full regressions.
Group B: actual PostgreSQL migration/reverse/drift, S3-compatible put/get/HEAD/checksum, actual clamd clean/EICAR/timeout, independent Worker process, concurrent claims, stale lease, retry/dead-letter/cancel, crash boundary, E2E staging → quarantine → approval-wait with real network dependencies.
Group C: object-store backup/restore, enterprise scanner/version/policy, organization IdP/Vault/network, final capacity/HA/DR/retention/UAT/security; all separately registered `DEFERRED_TO_PHASE_18` and not passed.
