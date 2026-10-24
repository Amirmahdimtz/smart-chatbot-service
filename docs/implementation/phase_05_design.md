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
- Idempotency: unique `(source, deployment_scope, owner, idempotency_key)`; same key and checksum returns original Job; changed payload is rejected. Within a source, a different idempotency key with the same checksum is rejected (409) rather than silently aliased. Replay of the original key with matching bytes returns the existing job. Source/checksum uniqueness prevents duplicate accepted content. Concurrency serialized by a locked Source row, not a process-global mutex.
- Persistence occurs before external storage upload: commit a `staging` job and object key, upload to `quarantine/{zone}/{opaque uuid}`, then mark `queued` only after put + integrity HEAD. Worker never claims incomplete staging. Stale committed staging intent is reconciled against the quarantined object's actual length/checksum and queued if intact; missing or corrupt content fails closed. Retries use the original idempotency key; no silent second write.
- All state transitions/audit events are transaction-bound; network I/O is never performed while holding a DB row lock. A crash after put and before acknowledgement creates a **durably discoverable** staging record, never an invisible, published object. Failed or abandoned storage is not treated as approved; garbage collection requires reviewed retention policy.
- Quarantine is the only bucket/prefix Phase 05 can write. No public ACLs, presigned downloads, public object references or Qdrant indexes. Scanning failure/timeout returns retriable error **without** changing to approval-ready.

## Provider and lifecycle choices
- S3-compatible object storage using pinned boto3 and environment-sourced disposable credentials; ingestion is disabled entirely outside synthetic internal development/integration. Immutable conditional S3 writes use If-None-Match: * with checked byte-identical replay. Storage bucket should have denied public ACLs, bucket policy, encryption/retention controls owned by deployer. CI uses community ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z; provenance/digest remain unapproved for organizational use.
- ClamAV `clamd` `INSTREAM` with bounded chunks, short socket deadline and response parsing. Only a literal clean result is approval-ready; FOUND is terminally rejected, unknown/timeout/unavailable is fail-closed. Do not log file bytes or daemon payload.
- Independent process `python -m src.host.ingestion_worker` composes existing DI, owns DB/storage/scanner startup/shutdown and bounded polling. Not FastAPI BackgroundTasks or in-memory queue.
- Multipart max-body is bounded at the ASGI edge; content additionally read in bounded chunks. Allowed Phase 05 formats should be *narrow* (validated UTF-8 text and structurally parsed digital PDF); ZIP/DOCX, archives, encrypted/invalid/oversized PDFs are rejected rather than decompressed. No OCR or extraction.
- Configuration is opt-in and fail-closed in ConfigReader; Phase05 test storage credentials come from ephemeral environment variables and never an implemented Vault storage integration. Change database revision-check atomically with migration and adjust baseline tests for the additive models/providers.

## Recovery and authorization
- Claim expiry/retry exhaustion must produce observable jobs with redacted error codes; heartbeat, cancellation and terminal transitions are compare-and-set by lease token; graceful stop stops polling and releases/lets expire lease.
- Identical retry of job processing is allowed but must never publish or mutate Qdrant. Check checksum while fetching quarantined object and before scan. Durable DB status survives request cancellation and worker restart.
- Controller uses existing auto-discovery and `SecurityService.authorize` with a dedicated permission; request Principal is resolved only from verified JWT middleware. Zone + owner checks occur again in Core/Repository. Validation errors expose codes only; audit excludes object bytes and secrets.
- Real-data access and publication stay disabled until separately signed D-07/D-08 and owning later-phase authorization. A/B tests use synthetic principals and a disposable network topology.

## Required verification
Group A: Ruff, imports/DI, config negative tests, size/signature/malformed PDF/multipart/filename/traversal/ZIP deny, authorization/isolation, state/idempotency/retry tests, OpenAPI contract, strict pip-audit, SBOM, secret scan, Docker build, full regressions.
Group B: actual PostgreSQL migration/reverse/drift, S3-compatible put/get/HEAD/checksum, actual clamd clean/EICAR/timeout, independent Worker process, concurrent claims, stale lease, retry/dead-letter/cancel, crash boundary, E2E staging → quarantine → approval-wait with real network dependencies.
Group C: object-store backup/restore, enterprise scanner/version/policy, organization IdP/Vault/network, final capacity/HA/DR/retention/UAT/security; all separately registered `DEFERRED_TO_PHASE_18` and not passed.

## Review amendment — object-staging crash recovery and retry policy

- `staging` DB intent is written and committed before the S3 PUT. On a crash after PUT but before queue acknowledgement, an independent worker inspects stale intents (age ≥30 seconds), reads only bounded quarantined bytes, re-verifies length and SHA-256, then atomically transitions `staging → queued`. Stale workers and duplicate reconcilers may read the same content but only one successful conditional queue transition occurs.
- For missing objects older than 300 seconds, the worker records `dead/staging_abandoned` and leaves the immutable identity/key for safe same-key retry. An S3 timeout/network outage does **not** mark staging complete or dead: the worker retries reconciliation without claiming approval. A corrupted object is `dead/integrity_mismatch`.
- A failed pre-processing storage PUT with `storage_unavailable` may be retried using the *same* idempotency key/checksum on the same existing job/version. Already processed or malware-dead jobs may not be rearmed. No object deletion/purge without approved D-08 retention.
- An expired final lease is marked `dead/lease_expired`; stale worker lease tokens cannot commit terminal success after expiry. Lease reclaim only if `attempts < max_attempts`.
- CI S3-compatible synthetic service currently uses a community-published MinIO-compatible container, not an organization-vetted image. The production storage product and supply-chain verification remain open infrastructure decisions; this image has no production authorization.

## Post-implementation hardening

Knowledge upload routes are not mounted unless the synthetic internal feature flag is enabled. TXT and PDF filename extensions must match their MIME type, with size/signature validation. S3 writes require scoped UUIDv4 object keys and use conditional create; an identical lost-ACK replay is safe, while changed bytes cannot overwrite via the adapter. An actual OS Worker process was killed after its PostgreSQL lease had been committed and the lease was reclaimed by another Worker, which scanned using real ClamAV. Current source-specific CI evidence and remaining tests are tracked in phase_05_evidence.md.


## Phase 05 verified CI boundary (2026-10-24)

Digest-pinned synthetic CI services have now passed real PostgreSQL, ClamAV and S3-compatible integration including three separate reversible Docker pause/unpause outages with recovery and persisted job checks (CI 40098823479, source 6fc7e39f39e2f5bd9ca8399ae7a03c809ae48ac0). These are not full process stop/recreation, organizational HA or DR tests. S3 and ClamAV test image digests were resolved from real CI Docker pulls and pinned in the workflow; community S3 image provenance has NOT received an independent approval. No organization connectivity, HR/PII, publication, Qdrant writes, UAT or production authorization is claimed.


## Valid PDF document type verification

Phase05 has real positive coverage for digital PDF generated by pinned pypdf and sent as application/pdf with .pdf filename; the file is bounded, structurally validated, quarantined and scanned by genuine ClamAV, leaving a persisted awaiting_approval document version without publishing. CI 40099162282 proves the path on disposable dependencies. OCR and content extraction remain Phase06 scope only.

## Phase 05 completion amendment — scoped synthetic source lifecycle, 2026-10-24

Only the synthetic-only fields are permitted for this pre-D-08 development scope: `classification="synthetic_unclassified"`, `policy_ref="synthetic-only"`. Both are constrained by Source DTO AND PostgreSQL CHECK constraints; they **must not be interpreted as approved organizational information classification or policy**. Source `max_file_bytes` is optional, checked at creation against the global upper bound, and enforced before upload streaming and again before staging. Source `disabled` prevents future uploads, is owner/zone-authorized and audited; existing queued scans may still end at `awaiting_approval` but nothing is published or purged. The only supported source type remains `file`.

Use the Architecture Guide layering: HTTP multipart `UploadFile` is consumed by the Application upload adapter, not by Core IngestionService. Structurally valid digital PDF is inspected in a child interpreter with a 4-second maximum process deadline, killed on timeout, and restricted POSIX CPU/address-space limits (with fail-closed subprocess return codes). This is an upload preflight, not Phase06 OCR/extraction. The DB startup only checks the uniquely configured current Alembic script head, never runs an implicit schema upgrade. `0002_ingestion` changes were made in an unmerged feature branch and verified on disposable fresh database only. Any older synthetic test schema must be explicitly reprovisioned, not destructively altered in a non-disposable environment.

[CI 40106419648](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40106419648) on `18b679283305b4c3f634be5ce55362557b8bf5dc` verifies A/B; see the latest `phase_05_evidence.md` section. Independent acceptance and CI-only OCI image residual-risk decision are outstanding; Phase05 is IMPLEMENTED_AWAITING_VERIFICATION, not CLOSED or Production READY.
