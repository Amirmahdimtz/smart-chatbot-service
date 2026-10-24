# Phase 04 Qdrant — safe development / recovery runbook

This runbook covers **disposable synthetic-data integration only**. Do not use these steps on organization/shared/production instances. Qdrant production release, organizational TLS/network segregation, multi-node restore, HA/DR, SLO and access-policy acceptance require the separate Phase 18 change process.

## Test-only prerequisites

- Docker, Python 3.12, pinned requirements (`qdrant-client==1.20.0`) and disposable Qdrant server `qdrant/qdrant:v1.20.0`.
- No HR/PII/organization knowledge and no real secrets. Use an ephemeral test API key, not a value committed to Git. GitHub CI hosts an isolated service and supplies a synthetic key.
- Never expose port 6333 publicly. The local example binds only loopback.

## Local testing (synthetic)

Create a disposable isolated Qdrant container using an ephemeral nonproduction API key stored only in environment. For POSIX shells:

```bash
export SCB_PHASE04_TEST_QDRANT_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
docker run --rm --name scb-phase04-test -d \
  -e QDRANT__SERVICE__API_KEY="$SCB_PHASE04_TEST_QDRANT_KEY" \
  -p 127.0.0.1:6333:6333 qdrant/qdrant:v1.20.0
export SCB_PHASE04_TEST_QDRANT_URL=http://127.0.0.1:6333
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/test_phase04_qdrant.py
docker stop scb-phase04-test
unset SCB_PHASE04_TEST_QDRANT_KEY SCB_PHASE04_TEST_QDRANT_URL
```

Do not execute the integration fixture against any URL other than `http://127.0.0.1:6333`. Each test uses a unique collection prefix, so older data is not touched.

## Configuration

Enable only when the owner-approved deployment has the correct zone and secret:

`SCB_QDRANT_ENABLED=true`, `SCB_QDRANT_ZONE=public|internal`, `SCB_QDRANT_URL=https://...`, exactly one of `SCB_QDRANT_API_KEY` (environment secret injection) or `SCB_QDRANT_VAULT_PATH` (Vault KV-v2 key `api_key`), `SCB_QDRANT_DIMENSION`, `SCB_QDRANT_COLLECTION_PREFIX`, `SCB_QDRANT_SCHEMA_VERSION`, `SCB_QDRANT_DISTANCE`, `SCB_QDRANT_TIMEOUT_SECONDS`, `SCB_QDRANT_MAX_RETRIES`, and `SCB_QDRANT_BATCH_SIZE`. Disabled by default. Actual embeddings/dimensions need D-03 selection.

- Startup fails closed on zone mismatch, missing/invalid key, service unavailable, or non-TLS endpoint outside development/integration.
- No HTTP endpoint is introduced by this phase. Search results are candidate metadata only; Postgres/Policy re-check must be enforced in the consuming future Core service.
- Do not include URL/key in logs, traces, exception bodies or issue reports.

## Collection rebuild / versioned cutover

1. Record approved source/index manifest and version, expected dimension, distance, index schema, visibility policy, checksum and scope before migration (owning Phase 07).
2. Create fresh collection `{prefix}_{zone}_v{next_version}`; never mutate an incompatible live collection. Build required indexed fields before ingestion.
3. Rebuild only with approved/synthetic input; verify point count, hashes, scoped queries and post-filter Policy eligibility.
4. Use an explicit `activate_collection_async()` from an authorized maintenance path to atomically move `{prefix}_{zone}_active` to the verified version.
5. Keep old collection and snapshot until rollback window closes. Roll back by explicitly restoring the alias to the prior compatible collection version; no automatic deletion.
6. Restore from snapshots **only in a disposable instance** for technical A/B rehearsal; keep alias/schema metadata separate. Organization multi-node restore and DR are C/Phase 18, with signed change and verified backup.

Failure behavior: a Qdrant outage prevents enabled startup and search; never serve unverified cached candidates. Invalid version/dimension blocks migration and must not silently recreate/overwrite existing data. No real-data migration or destructive operation without separate owner/security/operations approval.
