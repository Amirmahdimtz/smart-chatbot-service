# Phase 04 Progress — isolated Qdrant foundation

- Date: 2026-10-24
- Phase: PHASE_04, Qdrant Secure Deployment & Search Provider
- Before: NOT_STARTED
- Current: **CLOSED — TECHNICAL ONLY**
- Marker: `PHASE_04_CLOSED`
- Entry: ADR-0007 conditional development permission after PHASE_03_CLOSED (technical).
- Code: feat/phase04-qdrant, PR #1; initial Qdrant provider, Config, lifespan, real Docker CI and negative tests committed.
- Files: see PR #1 file diff; design in phase_04_design.md, evidence in phase_04_evidence.md, operations in docs/operations/phase04_runbook.md.
- Public/Internal: configured zone and collection contract; no production network or real-data access.
- Tests A/B: current-source [CI 40091297919](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40091297919) **5/5 SUCCESS** at SHA `29e846070dd1089321520222b39688219a5e7cb2`: Group A generic verify **43 passed/5 skipped**, lint/format/audit/SBOM/Docker/gitleaks PASS; Group B real Qdrant **7 passed**, isolated PostgreSQL **4 passed**.
- Group C: P18-P04-C01 through P18-P04-C10 deferred in central register.
- D-03/D-04/D-07/D-08: open; no final embedding schema, publication policy or identity source assumed.
- Tests A/B required missing: none within Phase04 synthetic foundation. Organization and model-based tests are not presumed executed.
- Technical acceptance: **TECHNICAL_ACCEPTED / PHASE_04_CLOSED** with [evidence](phase_04_evidence.md) and [review](phase_04_technical_acceptance.md).
- Production release status: NOT_READY.
- Phase 05: NOT_STARTED; explicit owner instruction remains necessary. No Group C test requested.



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
