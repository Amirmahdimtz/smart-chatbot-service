# Phase 04 — Evidence and verification log

**Baseline main:** `0b34f457bacfe4aba704ff01563fcd1c4e62a97c`, CI [40088833699](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40088833699) successful before Qdrant changes.
**Implementation:** `feat/phase04-qdrant`, [PR #1](https://github.com/Amirmahdimtz/smart-chatbot-service/pull/1).
**Technology:** Qdrant Server 1.20.0 and client 1.20.0.

## Historical first CI (DO NOT mark pass)

Commit `bac41b172c32e1b76c68ff377274b1d17124eed0`, [Actions 40089879822](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40089879822).

- `docker-build`: SUCCESS, including production image build.
- `verify`: FAIL (41 passed, 3 skipped, 1 failed): Phase 02 regression expected exactly 8 DI providers; new legitimate Qdrant provider increases count to 9.
- `qdrant-integration`: FAIL (4 passed, 1 failed); negative-credential test incorrectly treated SDK `AsyncQdrantClient` as an async context manager; server startup and authenticated health probe worked.
- `secret-scan`: FAIL **before scan**, because PR event now requires explicit `GITHUB_TOKEN` for `gitleaks-action`. This is **NOT** a vulnerability finding and **NOT** a passed scan.
- `postgres-integration`: see linked job result; not inferred from other jobs.

Root causes fixed in follow-up commit `04c806ec1c24987efe0260da737e9f334819ab82` (accurate DI count, explicit SDK close, action token, strict publication boolean). New CI evidence must be verified independently. This document must not be treated as evidence of technical closure.

## Tests A Executed + Actual Results

First CI failure above. Retest results are not yet documented here. Requirements: import/compile, Phase 01 validator, Phase 01–03 regressions, Ruff check/format, pip-audit strict, SBOM, Docker build, gitleaks, contract and negative tests, timeout/retry/DI.

## Tests B Executed + Actual Results

The first real CI Qdrant v1.20.0 service was provisioned with a disposable test API key and authentic collection health probe succeeded, but the integration test aborted before collection scenarios. End-to-end tests for collection, filtering, aliases, snapshot, recovery and incompatible schemas require complete repeat evidence from a later job.

## Tests A/B Required but Missing

As of this log version: green full PR CI, verified actual Qdrant operations, restore/rebuild drill, security/negative regression, re-run audit, CI evidence on final SHA. No Group C substitute is claimed.

## Tests C Deferred to Phase 18

`P18-P04-C01` – `P18-P04-C10` are recorded in [Phase 18 Register](phase_18_verification_register.md), all `DEFERRED_TO_PHASE_18`. No organization test has been run.

## Final current-source CI and technical acceptance (2026-10-24)

Implementation source SHA: `29e846070dd1089321520222b39688219a5e7cb2`.
GitHub CI [run 40091297919](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40091297919): **5/5 jobs SUCCESS**.

- Group A actual: `verify` **43 passed, 5 skipped, 1 known Starlette warning**; compile, Phase 01 validators, Ruff check + format, `pip-audit --strict` **No known vulnerabilities found**, CycloneDX SBOM SUCCESS; `docker-build` SUCCESS, `secret-scan` SUCCESS (`no leaks found`). Two historical synthetic CI-only secret-detection fingerprints are exempted narrowly in `.gitleaksignore`; no production secret was committed or exempted, and current CI keys are ephemeral per run.
- Group B actual: real authenticated Qdrant **v1.20.0** with qdrant-client **1.20.0**, `qdrant-integration` **7 passed** (auth-negative, collection/index/filters, stable IDs, batch preflight rejection, version rebuild/alias rollback, schema/index mismatch, snapshot creation, timeouts/retries/unavailability). Real PostgreSQL 16 CI `postgres-integration` **4 passed** and repeat migration/drift plus disposable test-only reverse/re-upgrade PASS.
- A/B required missing: **none** for approved, synthetic-only Phase04 technical scope; full actual organization Snapshot Restore, physical isolation, GPU/HA, final authorization policy and model benchmark **not asserted**.
- C deferred: `P18-P04-C01` to `P18-P04-C10`, all `DEFERRED_TO_PHASE_18` with owners/evidence; no Group C test executed.
- Technical DoD: **PASS (technical Phase04 synthetic foundation)**, reviewed in [phase_04_technical_acceptance.md](phase_04_technical_acceptance.md).
- Phase Before `NOT_STARTED` → After `CLOSED` technical only. Production Release: `NOT_READY`.

Historical failed runs above are retained and must not be confused with final successful run.

## Independent corrective re-audit — 2026-10-24

Source and exact integration evidence: [CI run 40092573876](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40092573876) on commit `b5c38e8e097f53a13faf23b557c8809d3be6c063`, branch `fix/phase04-independent-audit`: all **5/5 CI jobs SUCCESS**.

### Findings in the earlier technical closure (now addressed)

1. The original Phase 04 tests created Qdrant snapshots but did **not actually restore them**. The earlier claim of no missing Group A/B checks was overbroad for the plan's Phase 04 Restore/Rebuild/Backup Metadata criterion. The new **real Qdrant isolated snapshot recovery** test restores an actual snapshot to an independently named synthetic collection using `file://` and `SnapshotPriority.SNAPSHOT`, checks restored point identity and payload and confirms that snapshot recovery does not silently move aliases.
2. Collection provisioning caught all mapped failures and re-probed an unavailable collection; a single 404-only path and safe 409-creation conflict handling now distinguishes absence from errors and validates resulting schema.
3. Batch upsert returned point IDs using set iteration, losing caller order. Return order now follows input order, while duplicate identity remains rejected.
4. Backup manifest was not available. `backup_manifest_async` now captures snapshot name, version, dimension/distance, zone, source collection and active alias target; alias drift during snapshot capture fails closed. This is **a sidecar backup metadata contract**, not the still-undecided Phase 07 authoritative index manifest.
5. Additional real negative tests cover wrong-zone payload injection, malformed classification allowlist and concurrent collection bootstrap. No security-sensitive API was exposed by this phase.

### Tests A Executed + Actual Results

- Exact-source CI `verify`: **43 passed / 7 skipped / 1 existing Starlette warning**; compile, Phase01 validators, Ruff check and `format --check` (28 formatted files), `pip-audit --strict` (`No known vulnerabilities found`), SBOM generation/upload all PASS.
- `docker-build`: SUCCESS; `secret-scan`: SUCCESS / `no leaks found`. The two historical fingerprints for retired synthetic-only keys retain their narrow, auditable exemptions. Real test credentials are generated ephemerally per CI run.
- Prior corrective PR CI runs with Ruff failures remain historical FAIL evidence; this final green run supersedes them for acceptance, not retroactively converting them to PASS.

### Tests B Executed + Actual Results

- Actual disposable, authenticated Qdrant Server **v1.20.0**, qdrant-client **1.20.0**: `qdrant-integration` **9 PASSED**, including actual snapshot restoration, version cutover/rebuild/rollback, index mismatch, manifest alias capture, negative authorization filters, ordered upsert, retry and concurrent collection bootstrap. Current-source green CI is the equivalent approved Group B evidence; no owner workstation execution is claimed.
- Actual isolated PostgreSQL 16 `postgres-integration`: **4 PASSED**, repeated Alembic upgrade, drift check and test-only downgrade/re-upgrade PASS. This is a regression check, not proof of organizational database recovery.
- Real Qdrant snapshot recovery is in the single-node disposable test; **not** multi-node or production snapshot restore.

### Tests A/B Required but Missing

**None for the now-remediated isolated Phase 04 technical scope.** Final organizational IdP/Vault/network isolation, publication policy, HA/DR/load and hardware-driven model/index validation are Group C or future owning decisions/phases, not secretly assumed PASS.

### Tests C Deferred to Phase 18

All ten existing IDs `P18-P04-C01` through `P18-P04-C10` remain **DEFERRED_TO_PHASE_18**, none executed. No register statuses changed.

### Independent Technical DoD / phase conclusion

- **Phase 04 Technical DoD:** PASS after corrective review and same-source real integration.
- **Phase Status Before independent re-audit:** `CLOSED` (historical, with an overstated A/B completeness conclusion). **During remediation:** under technical re-review. **After evidence re-review:** `CLOSED` — corrected, technical-only acceptance. No prior source/history is erased.
- **Production Release Status:** `NOT_READY`. Organizational owner/security approval, real-data access and final Qdrant topology remain unapproved.
- **Phase 05 entry:** independent technical `CONDITIONAL_GO_FOR_DEVELOPMENT_ONLY` after the correction is merged and main CI passes. See ADR-0008. Does not start Phase 05 or change Phase 01/02 statuses.
- **Reviewer:** AI-assisted technical assessor; not a Security, Privacy, Infrastructure, Product or Release Owner sign-off.
