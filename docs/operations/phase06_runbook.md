# Phase06 — Extraction/OCR and Chunk Persistence Runbook (synthetic CI/development)

**Scope:** Synthetic only, isolated development/integration; no production access. Source baseline Phase05 PR#3. Phase06 PR#4 is stacked, draft, no merges. Architecture and controls: ADR-0010 and docs/implementation/phase_06_design.md.

## Preparation and health

- Select development + internal deployment, use only isolated synthetic PostgreSQL, authenticated S3-compatible quarantine and ClamAV; configure real local OCR binaries pdftoppm and tesseract with fas+ara+eng language packs. No corporate data/remote OCR; do not disable scanner.
- The Host worker entry point remains python -m src.host.ingestion_worker. Its PostgreSQL startup requires exact Alembic schema head; it does not silently migrate.
- The existing synthetic CI ingestion job provisions real PostgreSQL/S3/ClamAV; Phase06 adds OCR language binaries. Check pinned dependencies, integrity of OCI images, package licenses and supported offline distribution before production decisions.

## Disposable migration test / rollback

On a *verified disposable* integration database only:
1. python src/infrastructure/scripts/run_migrations.py --upgrade
2. python src/infrastructure/scripts/run_migrations.py --upgrade
3. python src/infrastructure/scripts/run_migrations.py --check
4. python src/infrastructure/scripts/run_migrations.py --downgrade-test-only
5. python src/infrastructure/scripts/run_migrations.py --upgrade
6. python src/infrastructure/scripts/run_migrations.py --check

Do not invoke downgrade on a non-disposable database. Migration 0003 adds nullable columns; a test-only rollback discards extraction mapping metadata. Quarantined original objects remain untouched. Protect any necessary backups before operational changes in Phase18.

## Worker state and failure recovery

- The existing durable job is leased with a time-limited token. It can finish only if token still matches and lease is valid.
- After SHA/storage check, real ClamAV clean verdict must precede DocumentExtractor subprocess. Any unavailable scanner or malware fails closed; no parser run occurs.
- Parser fails on malformed/encrypted/empty/corrupted PDF, OCR limit exceeded, DOCX invalid ZIP, oversized input/output or binary problems. No chunks are committed and document must NOT reach awaiting_approval.
- Controlled error code, no raw file contents, user filename, object key or secrets in logs. ClamAV/storage failures trigger bounded retry; parser timeouts are retriable within job budget. Persistent parser rejection leads to dead job/failed version with clean error code.
- Successful chunks, completed job and awaiting_approval version are a **single PostgreSQL transaction** after fenced lock. Crash prior to commit leaves no accepted chunks. Job restart/reclaim reruns deterministic chunks.
- Cancellation should terminate active extraction child. Lease expiry and stale tokens must not commit, even if a previous parser eventually finishes.
- Resuming a failed document requires an approved reprocessing workflow; do not manually reset terminal DB states or delete immutable quarantine objects.
- No publication, Qdrant indexing, embedding or retrieval is performed by this worker; approval and release remain other phases.

## Testing and evidence

Run source-matched compile/import/pytest/Ruff and CI real ingestion integration, capture branch/commit SHA and GitHub Actions run URLs. Real OCR synthetic Gold Fixture CER and page/source-span mapping must pass; Group B PostgreSQL+S3+ClamAV tests must verify persisted chunk rows. Compare PDFs/docx to raw page/text and ensure no guessed page for DOCX.

Record failures or skipped tests as NOT_RUN/FAIL rather than PASSED. No Group C On-Prem test before Phase18. For actual On-Prem OCR runtime, IdP/Vault, network, HA/DR, load/soak and organizational UAT see register P18-P06-C01..C06, all DEFERRED_TO_PHASE_18 until then.
