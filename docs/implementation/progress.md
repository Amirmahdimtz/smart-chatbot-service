# Smart Chatbot Service — Progress Register

> **Current policy interpretation — 2026-10-27 / v1.1.1:** The status table is a *snapshot*, not a list of mandatory organization-server test gates. For phases 01–17, only real required A/B tests, core dependencies, documentation, critical findings and approvals **genuinely required for that phase's technical Scope** govern `CLOSED — TECHNICAL ONLY`. Final On-Prem organization tests and Release/Operations/Security approval are Group C **solely in Phase18**. Historical paragraphs saying On-Prem testing blocked Phase02/03 are retained as historical evidence, not the current rule; see ADR-0006 and ADR-0009. This note changes **no phase status** without documented A/B re-review and a separate acceptance decision. Status of existing P18 verification IDs remains `DEFERRED_TO_PHASE_18`, never `PASSED`.

**Updated:** 2026-10-21 · **Phase:** PHASE_01 · **Status Before:** NOT_STARTED · **Status After:** IMPLEMENTED_AWAITING_VERIFICATION

**Marker:** PHASE_01_IMPLEMENTED_AWAITING_VERIFICATION

## Phase 01 evidence and gates

- Repository as-is: [discovery](repository_discovery.md); empty `main`, baseline SHA = N/A, created as part of Phase 01.
- Contract: [requirements](../requirements/requirements_contract.json), [architecture](../architecture/architecture_contract.json), [system](../architecture/system_architecture.md), [deployment](../architecture/deployment_architecture.md), [security](../security/data_access_matrix.md).
- Decisions: [ADR-0001](../decisions/ADR-0001-architecture-baseline.md), [ADR-0002](../decisions/ADR-0002-initialization-workflow.md), [ADR-0003](../decisions/ADR-0003-acceptance-governance.md); 20 deferred decisions with provisional phase-gate milestones, not confirmed owners or calendar deadlines, in the architecture contract.
- Evaluation: [evaluation](../evaluation/evaluation_plan.md); [development workflow](development_workflow.md); [source inventory (not yet supplied)](../requirements/source_inventory.md).
- Automated contracts: `scripts/validate_phase01.py`, `tests/test_phase01_contracts.py`. Owner-reported [Windows workstation verification](phase_01_workstation_verification.md) on `dd8e4dcf149fe59102a72030dc4b562642a6bb0a`: Python compile PASS, validator PASS (normal and `-O`), 12/12 unittests PASS (normal and `-O`), clean Git tree. Earlier 6/6 baseline and execution limitations are in [Phase 01 evidence](phase_01_evidence.md).
- Gate register: [phase 01 acceptance](phase_01_acceptance.json), [owner approval workflow](approval_workflow.md). Eight gates defined; G-08 has reproducible, owner-reported PASS test evidence, but formal Technical Verifier approval is still pending. G-01–G-07 require responsible-owner action. Security/architecture/product/domain approval: **AWAITING_APPROVAL**. No approved real corpora/SSO/HR policy/model/hardware/Agent contract.
- `CLOSED`: **No**. Final completion marker deliberately **not issued**.

## Phase status

| Phase | Status | Hard prerequisite / evidence gate |
|---|---|---|
| 01 | IMPLEMENTED_AWAITING_VERIFICATION | Updated validator/tests PASS on SHA `dd8e4dcf149fe59102a72030dc4b562642a6bb0a` per owner-reported Windows transcript; formal G-01–G-08 approvals, source inventory, policy and repository governance remain outstanding |
| 02 | IMPLEMENTED_AWAITING_VERIFICATION — awaiting phase-specific A/B re-review | Historical source-specific evidence: 36 pytest PASS on owner Windows checkout and CI (3/3 jobs), with Ruff and strict pip-audit PASS; see [Phase 02 evidence](phase_02_evidence.md). Determine whether all mandatory **isolated synthetic A/B public/internal/authz/smoke** requirements and genuinely applicable technical approvals are evidenced before a new closure decision. Organization IdP/Vault, actual Public/Internal firewall/TLS/network, HA/restore and operational Security/Release sign-offs are Group C **DEFERRED_TO_PHASE_18**, not Phase02 technical closure blockers. No implicit status change. |
| 03 | **CLOSED — TECHNICAL ONLY** | Reviewed source `33c215945676c9d84bca7b6511f059a7b3a6c171`, [CI run 40087999023](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40087999023): 4/4 success, 39 passed/1 skipped general tests; 4 passed isolated real PostgreSQL integration; migrations and audit PASS. [Technical acceptance](phase_03_technical_acceptance.md); Group C `P18-P03-C01`–`C06` [deferred to Phase 18](phase_18_verification_register.md). D-07/D-08 needed for real data; **NOT PRODUCTION_READY**. |
| 04 | **CLOSED — TECHNICAL ONLY** | [Phase 04 technical acceptance](phase_04_technical_acceptance.md), CI [40091297919](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40091297919): 5/5 jobs SUCCESS, 43 passed/5 skipped general, 7 real Qdrant, 4 real PostgreSQL; P18-P04-C01–C10 deferred. NOT_PRODUCTION_READY |
| 05 | **IMPLEMENTED_AWAITING_VERIFICATION — engineering A/B verified; explicit technical review approval pending** | On exact code HEAD `66c282b398842927e646f04efe292004f0afe1da`, [CI 40106739208](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40106739208) **6/6 SUCCESS**: Group A **78 passed/25 skipped** and isolated real Group B **10 ingestion + 8 recovery + 4 PostgreSQL + 9 Qdrant PASS**. `ADR-0008` explicitly requires independently accepted technical DoD; no such attributable review was found on PR #3. Synthetic CI-only SeaweedFS image risk is a separate **A/B risk disposition**, not organization Production Image approval. Real On-Prem tests are Group C **DEFERRED_TO_PHASE_18** and not a Phase05 blocker. No automatic `CLOSED`, PR still Draft and unmerged, production `NOT_READY`. |
| 06–14 | NOT_STARTED | Follow implementation plan dependencies |
| 15 | BLOCKED_EXTERNAL | Independent Agent API, auth, sandbox and E2E not yet supplied |
| 16–17 | NOT_STARTED | Prior phases; live Agent for side-effecting operations |
| 18 | NOT_STARTED | Full deployment/release verification |

## Open sign-offs

Architecture Owner; Security Owner; Product Owner; Religious Content Lead; HR Policy Owner; Research Office Lead; Employee Privacy Owner; Operations Manager; Repository Admin. Owner names and deadlines require formal assignment (no person is assumed).

## Next action

Phase 01 workstation compile, validator and 12/12 negative/unit tests were previously reported PASS for their validated SHA. Obtain attributable acceptance decisions for G-01–G-07 and Technical Verifier sign-off for G-08; resolve public repository classification, decision governance and source inventory (or approved deferrals). Phase 02 is implemented and has passed GitHub CI and the latest owner-reported 27-test Windows regression; finish organizational IdP/Vault/Public–Internal security checks, operational verification and owner sign-offs. No `CLOSED` marker until the corresponding gates are approved.

## Phase 02 development gate (2026-10-21)

Phase 02 independent implementation was authorized by an explicit GO_FOR_DEVELOPMENT exception, recorded in [ADR-0004](../decisions/ADR-0004-phase02-development-gate.md). Phase 01 formal approval G-01–G-08 is **not** implied or changed. Phase 02 evidence is in [phase_02_evidence](phase_02_evidence.md); deployment guidance is in [Phase 02 runbook](../operations/phase02_runbook.md). No Phase 01 CLOSED marker and no production approval have been issued.

## Phase 03 technical advance gate — conditional only (2026-10-24)

A Phase 02 technical re-audit resulted in [ADR-0005](../decisions/ADR-0005-phase03-conditional-development-gate.md): **conditional GO_FOR_DEVELOPMENT only** for Phase 03 independent PostgreSQL architecture/design and isolated implementation under a reviewed ERD and migration plan. This is an exception to assuming completed Phase 02 acceptance; **Phase 01 and Phase 02 remain IMPLEMENTED_AWAITING_VERIFICATION, Phase 03 remains NOT_STARTED**, and no production use, organizational identity integration or sensitive corpus is approved. Actual Phase 03 work starts only on explicit owner instruction, subject to checking dependencies and current repository baseline again.

## Phase 03 initiated (2026-10-24)

Explicit owner command received. Technical baseline `eb918b1f27c6028ca9d19c118973d8e165bb661f` verified on `main`; development-only ADR-0005 gate valid. Phase 03 development initiated and subsequently verified in [GitHub CI run 40078990354](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40078990354): 4/4 jobs PASS on `462411bfbb921cb52f6a2b0361631aee4c1a730d`; Phase 03 status `IMPLEMENTED_AWAITING_VERIFICATION`, pending Windows/On-Prem and stakeholder approval. No other phase status changed. No completion marker or organizational data authorization.

**Phase 03 marker:** `PHASE_03_IMPLEMENTED_AWAITING_VERIFICATION` (not CLOSED).

### Phase 03 verification follow-up (2026-10-24)

Latest source [`35bbff3ec9d5b806904b8c0be5427e8c92fd3fd7`](https://github.com/Amirmahdimtz/smart-chatbot-service/commit/35bbff3ec9d5b806904b8c0be5427e8c92fd3fd7) enforces deployment-zone scope in `ConversationService`, rejects empty production DB password, and extends BaseRepository transaction tests. [GitHub CI 40079517611](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40079517611): 4/4 jobs PASS, verify 38 passed/1 skipped, isolated real PostgreSQL 16.15 integration 3 passed; Alembic repeated upgrade, drift check and disposable test-only reverse/upgrade PASS; Ruff, strict dependency audit, Docker build and secret scan PASS. The skipped test in non-PostgreSQL verify is executed in the PostgreSQL-specific job. No Windows or organizational approval asserted. `PHASE_03_IMPLEMENTED_AWAITING_VERIFICATION` remains active; Phase 01/02 unchanged.

## Phase 03 owner-reported Windows verification (2026-10-24)

The project owner provided a Windows PowerShell transcript on **clean `main` SHA `61ad27287b34693314466d2727d9e676f1d0cb08`**. Python 3.12 requirements and `pip check` PASS; compile and both Phase 01 validators PASS; full suite **38 passed / 1 skipped** before and after isolated database testing; Ruff check and format PASS (26 files); actual PostgreSQL `postgres:16` test database `scb_phase03_test` initial/repeated Alembic upgrade, `0001_foundation` revision, `--check` without drift and **3/3 integration pytest PASS**. Initial immediate `pg_isready` reported `no response` before subsequent successful DB operations. Local strict `pip-audit` **INCONCLUSIVE** due `RemoteDisconnected`/network error, not a vulnerability finding; the source-matched GitHub CI audit previously PASS. Windows destructive test-only downgrade and true backup restore were **NOT_RUN**. [Full owner-reported evidence](phase_03_evidence.md).

**Status stays `PHASE_03_IMPLEMENTED_AWAITING_VERIFICATION`**, not `CLOSED`: On-Prem/Public–Internal isolation, TLS/roles, real restore/HA, D-07/D-08, acceptance sign-offs remain outstanding. Phases 01/02 are unchanged. No Phase 04 work started.

## Phase 03 subsequent Windows dependency security retest (2026-10-24)

The owner reran `python -m pip_audit -r requirements.txt --strict --timeout 60` in the `smart-chatbot-service` checkout on source SHA `61ad27287b34693314466d2727d9e676f1d0cb08` and reported **`No known vulnerabilities found`**. The previous Windows `RemoteDisconnected` run remains an accurately recorded failed attempt; the later complete strict audit is **PASS on the tested requirements at that point in time** (the transcript did not separately report a numeric exit code). All pinned `requirements-dev.txt` dependencies were also already installed successfully. [Detailed retest evidence](phase_03_evidence.md). The related GitHub CI [run 40084606410](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40084606410) was independently **4/4 jobs successful** after prior documentation-only updates.

Phase 03 retains `PHASE_03_IMPLEMENTED_AWAITING_VERIFICATION`: security scan success does **not** replace pending organization TLS/Public–Internal identity separation, backup/PITR restore, operational load/HA/DR tests or D-07/D-08 sign-off. Phase 04 remains `NOT_STARTED`.

## Phase 03 CLOSED — new technical review decision (2026-10-24)

**Important historical note:** Earlier sections above accurately describe their earlier review points (`IMPLEMENTED_AWAITING_VERIFICATION` and On-Prem blockers). They are **not** current Phase 03 status after v1.1.0 adoption and new evidence review. [ADR-0006](../decisions/ADR-0006-phase-closure-verification-v1_1_0.md) changes the verification scheduling policy without rewriting those prior decisions.

- Phase: `PHASE_03`; **Status Before** `IMPLEMENTED_AWAITING_VERIFICATION`; **Status After** **`CLOSED` (technical)**, marker **`PHASE_03_CLOSED`**.
- **Technical DoD Status:** APPROVED **for Phase 03 structural PostgreSQL foundation using synthetic test data only**. ERD/migration `0001_foundation` accepted as technical foundation, not approval of operational HR retention/publishing or D-07/D-08 policy.
- **Tests A Executed + Actual Results:** [CI 40087999023](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40087999023) on `33c215945676c9d84bca7b6511f059a7b3a6c171`: full verify 39 passed/1 skipped, 1 known warning; Ruff, compile, validators, strict pip-audit, SBOM, Docker and secret-scan PASS. CI 4/4 jobs SUCCESS.
- **Tests B Executed + Actual Results:** CI isolated actual PostgreSQL 16.15: 4/4 integration tests PASS, upgrade/repeated upgrade/drift and destructive **test-only** downgrade/re-upgrade PASS; historical owner Windows 38 passed/1 skipped and 3 real DB integration tests PASS on prior source. Current change additionally validated by same-source CI.
- **Tests A/B Required but Missing:** none for scoped technical foundation. D-07/D-08 decisions are pending for any real identity/retention/data/HR integration; no real-data feature was asserted ready.
- **Tests C Deferred to Phase 18:** six outstanding `DEFERRED_TO_PHASE_18` IDs `P18-P03-C01` to `P18-P03-C06` covering isolation, TLS/IAM/Vault, PITR/restore, controlled migration, capacity/HA and policy E2E in [Register](phase_18_verification_register.md). **None passed or executed**.
- **Production Release Status:** **NOT_READY** — Phase 18 tests and official owner approvals are mandatory.
- **Reviewer:** AI-assisted technical assessor authorized by the owner to review and sign off **technical evidence only**, no impersonation of Security/Privacy/Infrastructure sign-off. [Full rationale and limitations](phase_03_technical_acceptance.md).
- Phase 01/02 statuses are **unchanged**; Phase 04 is **NOT_STARTED**; new phase initiation requires explicit owner command.

## Phase 04 conditional technical entry gate (2026-10-24)

[ADR-0007](../decisions/ADR-0007-phase04-conditional-development-gate.md) records a **CONDITIONAL_GO_FOR_DEVELOPMENT_ONLY** after independent verification of the `main` source and the Phase 03 technical closure. [CI run 40088290757](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40088290757) completed **4/4 jobs SUCCESS** on the approved Phase 03 closure SHA `ce3def7094bafbd505dd51e4059b285ae7852d09`.

**Phase 04 remains `NOT_STARTED`.** Entry is authorized only for isolated, synthetic-data Qdrant development **after explicit owner instruction**. Phase 01 and Phase 02 remain `IMPLEMENTED_AWAITING_VERIFICATION`, and the exception does not approve their missing owner decisions. Phase 03 remains `CLOSED` (technical). Phase 04 Group A/B must include actual Qdrant Docker/CI Integration; Group C organization infrastructure tests are deferred **only to Phase 18** and must be registered with immutable IDs when Phase 04 is carried out. D-03/D-04 production embedding dimensions/sparse strategy and D-07/D-08 data policy/identity approval remain open. **Production Release Status: NOT_READY.** No Qdrant provider, migrations, test results or Phase 04 CLOSED marker is asserted by the gate review.


## Phase 04 implementation initiated (2026-10-24)

Owner's explicit command starts Phase 04 under ADR-0007 from verified main SHA `0b34f457bacfe4aba704ff01563fcd1c4e62a97c`. Development is on PR #1 `feat/phase04-qdrant`. The phase adds a real asynchronous Qdrant infrastructure boundary, synthetic-only CI integration, independent deployment-zone config/credential validation and planned versioned index/alias contract. Baseline CI [40088833699](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40088833699) passed; first Phase 04 PR CI [40089879822](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40089879822) had actual failures, documented in [Phase 04 evidence](phase_04_evidence.md) and addressed in subsequent commits. No `PHASE_04_CLOSED` marker until current-source A/B evidence is reviewed.

- Tests A: initial failures recorded; follow-up evidence pending.
- Tests B: genuine isolated Qdrant Docker container started; operation-level integration must be retested and evaluated.
- Tests A/B required but missing: current verified green full CI, real scoped query/index/alias/rebuild, bounded retries and schema incompatibility proof pending.
- Tests C: ten unique `P18-P04-C01`–`P18-P04-C10` records in the [Phase 18 Register](phase_18_verification_register.md), all `DEFERRED_TO_PHASE_18`.
- Technical DoD: pending; Phase Before `NOT_STARTED` → Current `IN_PROGRESS`.
- Prior statuses: Phase 01/02 unchanged; Phase 03 technically CLOSED.
- Production Release: NOT_READY. Phase 05 not started, requires explicit separate instruction.


## Phase 04 technical closure — independently reviewed (2026-10-24)

**Marker: `PHASE_04_CLOSED` — technical only, synthetic-data Qdrant infrastructure.**
- Owner start instruction and approved ADR-0007 scope; Phase Status Before `NOT_STARTED` → After `CLOSED` after implementation, corrections and independent review.
- Implementation source `29e846070dd1089321520222b39688219a5e7cb2` on PR #1. [CI 40091297919](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40091297919) 5/5 SUCCESS, details in [Phase04 evidence](phase_04_evidence.md) and [acceptance](phase_04_technical_acceptance.md).
- Tests A: compile, validator, Ruff check/format, unit/negative/regression (43 passed/5 skipped), pip-audit strict, SBOM, Docker and gitleaks PASS. CI historic failures preserved.
- Tests B: real Qdrant 1.20 isolated with synthetic data, auth/filter/rebuild/alias/index/schema/snapshot/timeout integration 7 passed; PostgreSQL 16 real integration 4 passed and migration/reverse/drift PASS.
- Tests A/B Required but Missing: none for Phase04 approved synthetic technical scope.
- Tests C deferred: `P18-P04-C01` through `P18-P04-C10` all registered `DEFERRED_TO_PHASE_18` with role owners, expectations, evidence. No organization test executed.
- D-03/D-04/D-07/D-08 and Phase01/02 approvals remain open/unchanged; no data publication, organizational security approval or model dimension finalization.
- Technical DoD PASS for this limited scope; AI-assisted technical review does not replace accountable organization Security/Operations signoff.
- Production Release Status: **NOT_READY**; Phase18 remains the only On-Prem production verification and release gate. Phase05 not started.


## Phase 04 independent corrective review (2026-10-24)

- Reviewer found missing actual single-node isolated Qdrant snapshot recovery in the **historical** closure tests, plus unsafe 404 reprobe behavior, unordered batch IDs and missing backup/alias sidecar metadata. No Group C test was considered a blocker; this was **Group A/B** remedial scope.
- Corrective source commit `b5c38e8e097f53a13faf23b557c8809d3be6c063` on PR #2. [CI 40092573876](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40092573876) **5/5 jobs SUCCESS**: Group A `verify` 43 passed/7 skipped, compile, validators, Ruff, strict dependency audit, SBOM, Docker, gitleaks PASS. Group B real Qdrant 1.20.0 9 passed (including snapshot RESTORE and concurrent bootstrap); real PostgreSQL 16 4 passed and disposable migration/drift checks PASS.
- **Tests A/B Required but Missing:** none in remediated Phase 04 synthetic technical scope. Earlier gap is explicitly documented, not hidden.
- **Tests C Deferred to Phase 18:** P18-P04-C01–P18-P04-C10 all unchanged `DEFERRED_TO_PHASE_18`; none executed.
- **Technical DoD Status:** PASS for corrected Phase04 technical scope. **Status Before re-audit:** `CLOSED` (historically overaccepted) → technical re-review → **Status After:** `CLOSED` (corrected technical acceptance).
- **Production Release Status:** `NOT_READY`. D-03/D-04/D-07/D-08 open; no real organizational data or public/internal network tests.
- **Phase 05:** `NOT_STARTED`; ADR-0008 grants conditional entry review for synthetic-only work **only after merge and main CI success**, with separate explicit project-owner start instruction required. Phase 01/02 statuses unchanged.

## Phase 05 initiated — development only (2026-10-24)

- Owner explicitly authorized Phase 05 under ADR-0008 `CONDITIONAL_GO_FOR_DEVELOPMENT_ONLY`. Baseline `main` `0c817b1886b1668576e2037394f4b2d5cbf4997b`; branch `feat/phase05-ingestion`, [draft PR #3](https://github.com/Amirmahdimtz/smart-chatbot-service/pull/3). Marker: **`PHASE_05_IN_PROGRESS`**.
- Reused Phase03 source/document/version and Phase04 isolation contracts; additive `0002_ingestion` Migration, S3 quarantine, real ClamAV INSTREAM, durable PostgreSQL job/lease/heartbeat/retry/audit, independent worker process and synthetic-only, deny-by-default scoped Source/Upload/Status/Cancel API. No public release, HR data, OCR, Qdrant indexing or document publication.
- **Tests A — historical source-specific evidence:** CI [40095593728](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40095593728) at `d769ff7c19b441e25ad678d3c7b45548cfbbdbb4`: full pytest **69 passed, 10 skipped**, compile, validators, Ruff, strict `pip-audit` (no known vulnerabilities), SBOM, Docker, secret scan PASS.
- **Tests B — historical source-specific evidence:** same CI `ingestion-integration` **3/3 PASS** with disposable real PostgreSQL, actual ClamAV/EICAR and S3-compatible service, independent Worker process; real Postgres/Qdrant regression PASS. CI [40095766199](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40095766199) has B success on subsequent code including crash-recovery cases, but overall failed due Ruff import-order lint. **These runs do not establish PASS for later SHAs; always inspect latest head's CI.**
- **Tests A/B Required but Missing:** final same-SHA full all-job green after crash-recovery changes, negative API malformed multipart and dependency outage/timeout failure-injection evidence, independent technical review, source S3 mirror trust assessment. Do not mark missing/unexecuted tests passed.
- **Tests C deferred:** `P18-P05-C01` through `P18-P05-C08`, each `DEFERRED_TO_PHASE_18` with owner roles/evidence; never run before Phase 18.
- **Phase status Before / After:** `NOT_STARTED → IN_PROGRESS`; Technical DoD pending (no signed independent acceptance). **Production Release Status: NOT_READY**; Agent Phase15 `BLOCKED_EXTERNAL`; D-07/D-08 `BLOCKED_DECISION`; Phase06 remains `NOT_STARTED`.

## Phase 05 evidence follow-up (2026-10-24)

CI 40098047270 on bf6137dc64761ba2120c79128d630c12ed8e9b49: six of six jobs passed. General A tests 74 passed/14 skipped; real B ingestion seven passed, PostgreSQL four passed, Qdrant nine passed; Ruff/compile/validators/strict pip-audit/SBOM/secret scan and Docker succeeded. Group A/B still require actual isolated dependency container stop/restart, community test S3 image provenance review and independent technical/security sign-off. Group C P18-P05-C01 through P18-P05-C08 remain DEFERRED_TO_PHASE_18. Phase05 before/after: IN_PROGRESS -> IN_PROGRESS, Technical DoD PENDING, Production NOT_READY. Details: phase_05_evidence.md. No prior phase status changed.


## Phase 05 technical evidence after Docker dependency fault injection

CI https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40098823479 on 6fc7e39f39e2f5bd9ca8399ae7a03c809ae48ac0: 6/6 jobs PASS. Tests A: 74 passed/17 skipped, compile/lint/strict audit/SBOM/secret scan/Docker PASS. Tests B: 7 live ingestion PASS plus 3 actual isolated service pause/unpause/recovery PASS, PostgreSQL regressions 4, Qdrant regressions 9. Required-but-missing: independent security/architecture acceptance, community CI S3 image provenance and any reviewer-mandated full process stop/recreate scenarios. Tests C remain all deferred IDs P18-P05-C01–C08. Technical DoD: PENDING; phase status before/after: IN_PROGRESS/IN_PROGRESS; Production Release: NOT_READY. All earlier phase statuses are unchanged and Phase06 is NOT_STARTED.


## Phase 05 latest functional baseline (2026-10-24)

GitHub CI 40099162282 on 5c9096ace5983a8876bb3f4a37ef1c4ef325d098: six of six CI jobs PASSED. Group A 75 passed / 18 skipped (one deprecation warning); Group B eight real ingestion and three actual reversible service-outage tests passed; PostgreSQL four and Qdrant nine regressions passed. Synthetic PDF positive multipart/storage/ClamAV acceptance path is now covered, in addition to previous malware, crash and negative cases. Source images for S3/ClamAV are SHA digest-pinned. Required A/B/approval outstanding: signed independent technical/security review, community image provenance and any separately required full process restart fault scenario. Group C IDs P18-P05-C01–C08 remain deferred. Phase05 stays IN_PROGRESS / Technical DoD PENDING / Production NOT_READY. Phase06 NOT_STARTED and past phase decisions unchanged.


## Phase 05 latest gate — 2026-10-24

On `d266c0c0454261769a6c74f3427244836f1ed578`, [GitHub CI 40100496685](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40100496685) returned **all 6/6 SUCCESS**. **Tests A Executed + Actual Results:** 75 passed, 21 skipped; compile, architecture validators, Ruff lint/format, strict dependency audit, SBOM, Docker build, secret scan PASS. **Tests B Executed + Actual Results:** 8 real S3/ClamAV/PostgreSQL Ingestion E2E, 6 real dependency outage/recovery including 3 cold process restarts, 4 PostgreSQL and 9 Qdrant integration checks PASS. **Tests A/B Required but Missing:** accountable independent Architecture/Security sign-off, approval or replacement of third-party CI S3 image; actual container remove/recreate NOT_RUN pending reviewer DoD classification. **Tests C Deferred to Phase 18:** organization-only controls with IDs `P18-P05-C01`–`P18-P05-C08` remain `DEFERRED_TO_PHASE_18`. **Technical DoD Status:** `PENDING_INDEPENDENT_REVIEW`; **Phase Status Before/After:** `IN_PROGRESS → IN_PROGRESS`; **Production Release Status:** `NOT_READY`. Group C is not a blocker for Phases 01–17, but the remaining technical review gates are.

[Phase05 Evidence](phase_05_evidence.md), [Technical acceptance](phase_05_technical_acceptance.md), [Supply-chain risk review](phase_05_supply_chain_review.md). PR #3 remains Draft; no new phase was started.

## Phase 05 latest engineering verification — 2026-10-24


## Latest source-matched full A/B evidence — 2026-10-24

**Implementation SHA:** 15f4326cd5dba898a185dd95f067969ca90aa01c; **GitHub CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40103038011; all **6/6 jobs SUCCESS** on this exact SHA.

**Tests A Executed + Actual Results:** General pytest 75 passed / 24 skipped / 1 third-party deprecation warning; compile, normal/optimized architecture validators, Ruff lint/format, strict Python pip-audit (no known known vulnerabilities for audited Python dependencies), CycloneDX SBOM, Docker build and secret scan SUCCESS. All skipped service-specific tests were executed in separate Group B jobs and are not counted as A passes.

**Tests B Executed + Actual Results:** 9 real S3+ClamAV+PostgreSQL ingestion PASS, including synthetic PDF, actual malware EICAR, auth/idempotency/file negatives, real worker crash/recovery, and denied incorrect/anonymous S3 credentials. 8 real disposable dependency outages PASS: 3 Docker pause/unpause, 3 genuine process cold restarts, 2 whole-container remove/recreate (S3 retains immutable quarantine bytes on named volume, ClamAV requires a fresh real scan). PostgreSQL regression 4 PASS; Qdrant regression 9 PASS. Migration repeat-upgrade/schema drift/test-only reverse/re-upgrade PASS.

**S3 CI image:** Upstream SeaweedFS 4.48, registry-pinned exact image digest sha256:4e61d15fd35994cb1e43e1e553dff106794841fd9a99ade2fc8c8bfce4d7872d. Before using the service, actual CI cosign verification PASSED for GitHub Actions OIDC issuer, upstream seaweedfs/seaweedfs release workflow at refs/tags/4.48, trusted certificate authority and transparency log. Prior Coollabs third-party MinIO CI image was replaced. Signature provenance does NOT constitute a complete OCI image vulnerability/license/security approval.

**Tests A/B Required but Missing:** Independent, attributable Architecture + Security source review/sign-off and accountable synthetic CI-only image residual-risk disposition remain NOT_SIGNED. No known essential scoped code-path A/B execution gap remains after current checks; an independent reviewer may demand additional A/B checks if a new issue is identified. Full enterprise PostgreSQL node replacement/backup/PITR/HA/DR is Group C in Phase18, distinct from successful Group B in-flight leased-job recovery during true PostgreSQL process restart.

**Tests C Deferred to Phase 18:** P18-P05-C01 through P18-P05-C08 each remain DEFERRED_TO_PHASE_18, NOT_RUN and not PASSED. No corporate server was accessed.
**Phase 18 Verification Register IDs:** P18-P05-C01, P18-P05-C02, P18-P05-C03, P18-P05-C04, P18-P05-C05, P18-P05-C06, P18-P05-C07, P18-P05-C08.
**Technical DoD Status:** PENDING_INDEPENDENT_REVIEW. **Phase Status Before/After:** IN_PROGRESS -> IN_PROGRESS. **Production Release Status:** NOT_READY. D-07/D-08 organizational-data decisions remain blocked.

Historic intermediate CI failures (formatter, unpublished image tag, unsigned-image test setup, temporary malformed workflow) were corrected and are not represented as passed.


## 2026-10-24 final phase05 engineering hardening A/B evidence

**Verified code SHA:** `18b679283305b4c3f634be5ce55362557b8bf5dc`; **exact-source CI:** [40106419648](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40106419648), all **6/6 jobs SUCCESS**. Owner authorized the AI implementer to continue the technical completion and requested this review. This records owner direction only; it does **not** constitute a separately sourced independent Architecture/Security review or a signed approval by those accountable roles.

**Tests A Executed + Actual Results:** 78 passed, 25 skipped, 1 third-party warning. Compile, optimized/normal architecture validations, Ruff import/style checks, strict Python dependency pip-audit, SBOM, Docker image build, Gitleaks SUCCESS. The 25 skipped tests are not labeled PASSED; B executed genuine integration in its own jobs.

**Tests B Executed + Actual Results:** 10 real authenticated S3/ClamAV/PostgreSQL ingestion tests PASS including **new** Source synthetic classification/policy metadata, source-specific 1KiB upload guard and owner-only idempotent Source disable with negative foreign-owner and post-disable upload tests; existing actual digital PDF/EICAR/scanner/worker/lease and denial paths PASS. 8 genuine dependency outage/recovery tests PASS including three pause/unpause, three process cold restarts and two complete S3/ClamAV container remove/recreate. PostgreSQL regression 4 PASS; Qdrant regression 9 PASS. Additive `0002_ingestion` migration upgrades, repeat/drift and isolated test-only downgrade/reupgrade PASS. Actual upstream SeaweedFS immutable digest signature verified via CI Cosign before server startup.

**Gap remediation:**
1. Source contract now persists immutable, narrowly synthetic `classification = synthetic_unclassified`, `policy_ref = synthetic-only`, owner/domain/source_type/status and optional owner-configured max_file_bytes; none grants organization Policy/ACL privileges. D-07/D-08 **remain undecided** for real data.
2. Source `POST /sources/{id}/disable` is owner-only, audited and idempotent; disallow new uploads once disabled. It does not automatically purge/terminate already accepted jobs or issue publication rights.
3. Digital PDF preflight is in a separate interpreter process, with subprocess kill on 4-second deadline and POSIX 256MiB address-space/CPU resource ceilings; no uncancellable in-process PDF parsing Thread. The subprocess does not replace antivirus, and Windows lacks POSIX resource ceiling but enforces subprocess deadline. Extra A negative test confirms timeout fails closed.
4. `UploadFile` parsing is now confined to Application adapter and the Core service takes normalized bytes/metadata, honoring layering. Postgres revision gating dynamically matches Alembic ScriptDirectory's unique head while keeping migration execution explicitly out of startup.
5. `0002_ingestion` was edited **before first merge** and tested only on fresh disposable CI data; any private test DB already provisioned from the former unmerged definition must be discarded/recreated, never silently migrated in place.

**Tests A/B Required but Missing:** No known unrun mandatory scoped A/B test following these changes. **Independent accountable Architecture + Security source review, and written CI-only SeaweedFS OCI vulnerability/license/runtime risk disposition are still NOT_SIGNED**; verifier may request additional targeted evidence. A green CI and AI self-review are not an independent signature.

**Tests C Deferred to Phase18:** `P18-P05-C01`–`P18-P05-C08`, each `DEFERRED_TO_PHASE_18`, NOT_RUN/NOT_PASSED. **Phase18 Verification Register IDs:** P18-P05-C01, C02, C03, C04, C05, C06, C07, C08 (all prefixed P18-P05-).

**Technical DoD Status:** `PENDING_INDEPENDENT_REVIEW`. **Phase Status Before/After:** `IN_PROGRESS → IMPLEMENTED_AWAITING_VERIFICATION` (engineering/tests finished, not CLOSED). **Production Release Status:** `NOT_READY`; PR #3 still Draft/unmerged; no corporate data or On-Prem test conducted.


## Phase 06 — Dependent Persian Processing / OCR / Chunking (2026-10-27)

**Authorization:** GO_FOR_PHASE06_DEVELOPMENT_ONLY, Project Owner. This does not imply independent acceptance or Production.
**Status Before:** NOT_STARTED.
**Status After at engineering start:** IN_PROGRESS; **Marker:** PHASE_06_IN_PROGRESS.
**Repository:** main 0c817b1886b1668576e2037394f4b2d5cbf4997b; source baseline Phase05 PR #3 head 26dc557fb432d8830cdb522009f795d96aabdc54. Stacked Phase06 PR #4 (Draft) targets feat/phase05-ingestion, does NOT merge PR #3.
**Phase05 dependency:** IMPLEMENTED_AWAITING_VERIFICATION, exact-head CI 40464098716 6/6 SUCCESS; ADR-0008 independent technical acceptance not signed, synthetic-only OCI runtime/license risk disposition pending. No prior phase state modified.
**Implemented development scope:** Real bounded PDF text/OCR, DOCX/FAQ/table transcript and TXT extraction via child, reversible/Persian normalization preserving original, structure-aware deterministic UUIDv5 chunks, true extracted-source page/offset traces, engine/normalizer/chunker versions, incremental 0003 knowledge_chunk migration and lease-fenced atomic chunk persistence in existing scanned worker. Zero automatic publishing/Qdrant indexing. Data synthetic-only.
**Early observed Group A/B evidence:** Exact code SHA 4f9bf086ea3758a3caaa231c35a30d1deb139b33, GitHub Actions 40468179266 6/6 SUCCESS: Group A 86 passed / 25 skipped, strict Ruff/dependency-audit/SBOM/secret/Docker success; Group B real ingestion 10 and outage 8, PostgreSQL 4, Qdrant 9 passes. Later code/metadata/fixture additions require their own exact-SHA CI confirmation; these earlier results do not validate later commits.
**Tests A/B Required but Missing at status entry:** Latest-head full A/B result and independent technical/quality review; see phase_06_test_matrix.md and phase_06_evidence.md for updated evidence and any failures.
**Tests C Deferred to Phase18:** P18-P06-C01 through C06, all DEFERRED_TO_PHASE_18 and NOT_RUN. No server test requested.
**Technical DoD:** PENDING_SAME_SHA_AB_AND_REVIEW.
**Production Release:** NOT_READY; D-07/D-08 policy approval not granted.


### Phase 06 engineering handoff update — 2026-10-27

**Latest verified implementation SHA:** 289f216ca4f6e77d30211064e6bb0202ad2fd182; **CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40470440670, **6/6 jobs SUCCESS**. Detailed reproducible commands, runners, parser/OCR versions, CER and tests: phase_06_evidence.md. Group A 90 PASSED/27 SKIPPED; actual Group B 12 real ingestion, 2 real fa/ar OCR Gold Fixtures (each synthetic CER 0.000), 8 dependency outage/recovery, 4 PostgreSQL and 9 Qdrant PASSED. Skips are not PASSED.

**Phase Status Before / After:** NOT_STARTED → IMPLEMENTED_AWAITING_VERIFICATION (after independently reproducible scoped engineering verification; applicable accountable technical/quality acceptance still pending). **Marker:** PHASE_06_IMPLEMENTED_AWAITING_VERIFICATION. The earlier PHASE_06_IN_PROGRESS entry is a chronological record, not the current development handoff state.

**Technical DoD Status:** ENGINEERING_AB_VERIFIED — ACCEPTANCE_PENDING. Phase05 remains IMPLEMENTED_AWAITING_VERIFICATION under ADR-0008; unmerged Phase05 Draft PR#3 is unchanged. Actual independent specialist review, synthetic OCI/image/package risk disposition and representative OCR/layout quality acceptance not yet signed. D-07/D-08 do not authorize organizational data. Do not mark Phase06 CLOSED or release solely on CI success.

**Tests C Deferred to Phase18 / Register IDs:** P18-P06-C01, C02, C03, C04, C05, C06, each DEFERRED_TO_PHASE_18 / NOT_RUN; no corporate On-Prem tests required now.

**Production Release Status:** NOT_READY; Phase18 release/Group C gates and applicable owner approvals remain outstanding. Phase06 PR#4 is stacked Draft onto PR#3; no automatic merge.


### Phase 06 corrective verification — 2026-10-27

**Authorization:** GO_FOR_PHASE06_DEVELOPMENT_ONLY. Only Phase06-dependent Draft branch changed. Phase05 PR#3 and main remain unmerged/unchanged.

**Verified code SHA:** `730a04d807f2ced5a5ac61696cb97704a1886101`. **Actual GitHub CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40475859190 **6/6 jobs SUCCESS**. A = 93 PASS / 28 SKIP; B = 13 real ingestion, 2 real synthetic fa/ar OCR, 8 real outage/recovery, 4 real PostgreSQL, 9 real Qdrant PASS. Earlier CI 40475287944 had 2 real outage failures; a bounded write-readiness retest addresses this without ignoring or marking the former failures PASS. Evidence: phase_06_evidence.md.

**Changes:** Worker forwards `ProcessingSettings` into extraction subprocess; hybrid digital+raster PDF invokes local OCR within page/resource budget and preserves real raw text offsets; pre-accepted jobs from a disabled source remain processable per documented Phase05 policy, while future uploads are denied. New A/B tests cover these behaviors, and Phase06 Design/Test Matrix/Runbook are updated.

**Tests A/B Required but Missing:** independent attributable Phase06 technical/security/quality acceptance, domain-representative Arabic/Persian OCR/layout corpus and risk decisions D-10/D-12; inherited Phase05 independent ADR-0008 acceptance and synthetic CI-only image-risk decision are still pending. Group C `P18-P06-C01..C06` remains deferred/not executed.

**Technical DoD:** `ENGINEERING_AB_VERIFIED — ACCEPTANCE_PENDING`.
**Phase Status Before/After:** `IMPLEMENTED_AWAITING_VERIFICATION → IMPLEMENTED_AWAITING_VERIFICATION` (no CLOSED marker).
**Production Release Status:** `NOT_READY`. No Phase18 tests claimed.


## Phase07 — initial implementation / 2026-10-27

**Authorization:** owner explicitly requested Phase07 start. **Branch:** feat/phase07-index-lifecycle stacked on feat/phase06-persian-processing at SHA 3f4643143012da7aa029fba382cde7fc1ca04215; PRs #3/#4 unchanged and unmerged.

**Technical implementation:** Phase06 multi-page extraction offsets corrected in dependent branch only with regression; initial deterministic manifest and strict embedding vector validation in Core; actual QdrantProvider-based bounded synthetic-only staging with published=false, batch replay test and synthetic authenticated Qdrant Group B test added. This does NOT constitute model embedding, durable job, atomic publication or final index/reindex implementation.

**Tests A Executed + Actual Results:** pending PR-head GitHub CI; NOT YET REPORTED PASSED.
**Tests B Executed + Actual Results:** pending CI Group B Qdrant; actual model benchmark and publication/outage E2E not run.
**Tests A/B Required but Missing:** D-03 at least two genuine model benchmarks and approved model/dimension/metric/license, D-04 sparse strategy, real encoder/batch warmup, durable PG indexing jobs and manifests, consistency readback/retry, source-revision and model-revision-safe reindex/alias rollback, fenced publish/revoke, no stale citation and independent acceptance.
**Tests C Deferred to Phase18:** P18-P07-C01 through P18-P07-C07, NOT_RUN/NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P07-C01, C02, C03, C04, C05, C06, C07.
**Technical DoD:** IN_PROGRESS / FULL_SCOPE_NOT_IMPLEMENTED.
**Phase Status Before/After:** NOT_STARTED → IN_PROGRESS.
**Production Release Status:** NOT_READY. No production data or organizational server tests, no PR merge.

### Phase07 kickoff A/B evidence — 2026-10-27

**Exact tested source SHA** `e4e4bc522470402089e97f8e9842011ed759dc20`. **GitHub Actions 40482953105**: https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40482953105 — **6/6 jobs SUCCESS** after a previous failed Ruff-format-only run 40482772838. Group A **103 PASS / 29 SKIP**; Ruff, Compile, strict pip-audit, Docker, SBOM and secret scan PASS. Group B real isolated Qdrant old 9 PASS and new Phase07 hidden-stage 1 PASS with **synthetic numeric vectors (NOT actual embedding output)**, actual ingestion 13 PASS, genuine OCR 2 PASS, recovery 8 PASS, PostgreSQL 4 PASS and schema migration/drift/reverse checks PASS.

**Tests A/B Required but Missing:** two or more real candidate model benchmark runs and model selection D-03, sparse choice D-04, real model provider, durable PG index Job/Manifest with retry/fence and consistency, indexed version cutover and safe publish/revoke, versioned reindex and rollback, source-model drift tests and attributable independent technical acceptance. Full Phase07 DoD not satisfied.
**Tests C Deferred to Phase18:** P18-P07-C01..C07, all NOT_RUN/NOT_PASSED.
**Technical DoD:** INITIAL_ENGINEERING_AB_VERIFIED — FULL_SCOPE_IN_PROGRESS.
**Phase Status Before/After:** NOT_STARTED → IN_PROGRESS.
**Production Release:** NOT_READY.


### Phase07 D-03 genuine candidate execution — two real CPU runs on 2026-10-28

Draft PR #10 (no merge) now has **actual** two-model repeated GitHub CPU inference, not merely a planned benchmark. Tested SHA `c7669d764eedcda135380f4192336db6fa824ee2`, CI https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40655542808 **8/8 SUCCESS**; tested SHA `412ff5bfaccafe92734583106b364c4192108454`, CI https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40655824049 **8/8 SUCCESS**. Earlier invalid zero-job push workflows and Ruff failure are retained in original evidence and NOT counted successful.

**Tests A Executed + Actual Results:** both `verify` runs **106 PASS / 29 SKIP**, Ruff, Compile, strict pip-audit, SBOM, Docker and Secret Scan success.
**Tests B Executed + Actual Results:** actual pinned-weight model load, 384D embedding, query/passage CPU inference and measured Recall@1/3/5, MRR/nDCG, p95 and RSS for both E5-small and multilingual MiniLM-L12-v2 repeated twice; identical weights/dataset SHA across their two runs. Original isolated real PostgreSQL/Qdrant/Ingestion regression jobs also passed. E5 and MiniLM each Recall@1=0.941176, Recall@5=1.0, MRR@10=0.970588 and nDCG@10=0.97829 on only 17 positively labeled synthetic questions. CPU p95 speed advantage was NOT stable across separate CI runners.
**Tests A/B Required but Missing:** independent authorized Persian Gold Set, legal/license approval, model selection D-03, true Embedding Provider, D-04 sparse decision, actual durable Indexing, atomic Publication/Revoke/Reindex and expert acceptance. No Qdrant ANN, GPU or no-answer abstention benchmark is claimed.
**Tests C Deferred to Phase18:** P18-P07-C01..C07 DEFERRED_TO_PHASE_18 / NOT_RUN / NOT_PASSED.
**Phase 18 Verification Register IDs:** P18-P07-C01, C02, C03, C04, C05, C06, C07.
**Technical DoD Status:** REAL_D03_SYNTHETIC_CPU_BENCHMARK_B_VERIFIED; PHASE07_FULL_DOD_NOT_SATISFIED.
**Phase Status Before/After:** IN_PROGRESS → IN_PROGRESS.
**Production Release Status:** NOT_READY.
