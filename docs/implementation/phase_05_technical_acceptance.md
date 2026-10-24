# Phase 05 — Independent Technical Acceptance gate

Status: **PENDING — NOT SIGNED**. Owner authorized implementation only via ADR-0008, not an automatic `CLOSED` or production approval.

| DoD control | Evidence at time of this draft | Gate |
| --- | --- | --- |
| Existing Host/Application/Core/Infrastructure DI and no unnecessary new layer | Code exists in PR #3; manual review still needed | PENDING_REVIEW |
| Additive migration/reverse/drift and actual Postgres | CI 40095593728 PASS for historical SHA; newest code must be retested | PENDING_SAME_SHA |
| Quarantined object + actual clamd/real separate Worker | CI 40095593728 3/3 PASS (historical) | PENDING_SAME_SHA |
| Crash recovery, retry/dead letter, fences, cancellation | New code and synthetic tests are committed; no independent signoff | PENDING_REVIEW |
| Negative API AuthZ/MIME/oversize/archives, secret scan | Initial A tests and repo security tests; missing expanded E2E fault injection | PENDING_EVIDENCE |
| Full tests A/B actual results and complete regression | Historical CI success; latest verification required | PENDING_SAME_SHA |
| Runbook/recovery/documentation and Group C register | Docs added; Group C IDs P18-P05-C01..C08 deferred | PENDING_REVIEW |
| Critical security / D-07/D-08 data restrictions | Real organization data, approval, publication all forbidden | DEVELOPMENT_ONLY |

Technical verifier: **not assigned / no external approval signed**. Review owner role: independent Senior Backend/Architecture + Security. This document is a gate, not a fabricated independent acceptance.

Decision: **DO NOT MERGE / DO NOT CLOSE** while any required control is pending. Re-evaluate current head SHA and CI evidence before acceptance. Phase06 remains NOT_STARTED, production NOT_READY.

## Extended A/B review update

CI 40098047270 on source bf6137dc64761ba2120c79128d630c12ed8e9b49 succeeded in all six jobs: Group A 74 passed/14 skipped, Group B seven live ingestion, four PostgreSQL and nine Qdrant passes; strict audit, Ruff, SBOM, Docker and secret scan succeeded. Real worker termination after lease commit, real ClamAV malware scan, S3 conditional create, retry/fencing and negative API paths were exercised. This replaces historical PENDING_SAME_SHA notes for that precise source, not the outstanding external approval.

Remaining mandatory DoD: actual disposable service stop/restart under in-flight operations for each integration dependency; provenance and digest review of the community S3-compatible CI image; independent accountable architecture/security reviewer sign-off. Do not close Phase05 or merge the PR merely because CI is green. Owner roles and sign-offs are not fabricated. Technical DoD: PENDING; Phase Status: IN_PROGRESS; Production: NOT_READY.


## Status after actual synthetic outage verification

All six CI jobs in run 40098823479 PASSED on source 6fc7e39f39e2f5bd9ca8399ae7a03c809ae48ac0: general 74 passes/17 skips; ingestion 7 real tests and 3 real reversible outage/recovery tests; PostgreSQL 4 passes, Qdrant 9 passes; Ruff/compile, SBOM, dependency audit, Docker build and secret scan PASS. S3 and ClamAV container digests are pinned to registry digests obtained from CI. Actual pause/unpause with denial and recovery is proven, NOT a complete service process stop/recreate test.

Unresolved: independent accountable security/architecture review, provenance assessment/attestation for the community S3 CI image, and any separately deemed essential full stop/recreate fault injection. No Technical Verifier signature has been provided. Decision remains DO_NOT_CLOSE; PR #3 stays Draft; no merger or Production authorization. All P18-P05-C01–C08 deferred controls remain pending until Phase18.


## Latest verification baseline prior to independent sign-off

Source 5c9096ace5983a8876bb3f4a37ef1c4ef325d098 (CI 40099162282) has all six jobs successful, including 75 Group A test passes (18 skips) and real B 8 ingestion + 3 reversible Docker outage passes, plus PostgreSQL 4 / Qdrant 9 regressions. Successful digital PDF E2E is evidenced rather than assumed. Ruff, vulnerability audit, SBOM, Docker and secret scan passed. Image digests remain pinned.

There is no independent accountable reviewer signature or organizational policy approval. Production and publication remain prohibited. The PR must remain Draft; do not mark Phase05 CLOSED unless the verifier accepts all A/B evidence, the community image provenance and determines whether true cold restart tests are essential. Technical DoD PENDING; Production NOT_READY; Group C deferred to Phase18.


## Current technical gate after real cold process restart tests (2026-10-24)

**Latest tested implementation commit:** [d266c0c0454261769a6c74f3427244836f1ed578](https://github.com/Amirmahdimtz/smart-chatbot-service/commit/d266c0c0454261769a6c74f3427244836f1ed578); **CI:** [40100496685](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40100496685), all **6/6 jobs SUCCESS** on that exact code SHA.

| DoD category | Verifiable result | Current decision |
| --- | --- | --- |
| Group A and security regression | General `75 passed / 21 skipped`; compile/contract validators, Ruff check and format, strict pip-audit with no known vulnerabilities, SBOM, secret scan and Docker build SUCCESS | EVIDENCED, skips not passes |
| Real isolated Group B ingestion | `8 passed`, genuine S3 quarantine, PostgreSQL, ClamAV, signed synthetic auth, digital PDF, EICAR, API negatives and separate Worker | EVIDENCED |
| Real isolated Group B outage and restart | `6 passed`: 3 reversible pause/unpause + 3 Docker cold **process** restarts (S3 object bytes preserved, ClamAV clean/EICAR after restart, PostgreSQL in-flight lease persisted and stale token fenced) | EVIDENCED |
| Other regression Group B | PostgreSQL `4 passed`, Qdrant `9 passed`; migration repeat/upgrade/drift/disposable reverse successful | EVIDENCED |
| Community S3 test-image trust decision | Digest matches public GHCR package listing; public source/build scripts inspected, but signature, provenance attestation, dependency vulnerability and risk-owner approval are **NOT** evidenced | PENDING_SECURITY_ACCEPTANCE; see [supply-chain risk review](phase_05_supply_chain_review.md) |
| Container removal/recreation, not just process restart | `docker restart` proven; `docker rm` plus provision-new-container while actively processing not executed; reviewer must decide if this is essential additional Group B evidence | PENDING_REVIEW_DECISION; NOT_RUN if required |
| Independent accountable Senior Backend/Architecture + Security sign-off | No attributable verifier or approval was provided | NOT_SIGNED |

**Technical DoD Status:** `PENDING_INDEPENDENT_REVIEW`, not `CLOSED`.
**Phase Status Before/After:** `IN_PROGRESS → IN_PROGRESS`.
**Production Release Status:** `NOT_READY`, no real data, no publication/organization authorization.
**Tests C Deferred to Phase 18:** `P18-P05-C01` through `P18-P05-C08`, all `DEFERRED_TO_PHASE_18`, none executed. D-07/D-08 remain blocked decisions.

### Decision requested from an actual technical reviewer

The reviewer must independently inspect source/security boundaries and the exact CI evidence, decide whether the recorded supply-chain risk is acceptable for synthetic CI or demands an approved image, decide if true container destruction/recreation is mandatory Group B, and record an attributable approval or rejection (identity, role, timestamp, commit, any conditions). **No sign-off has been simulated or delegated to CI/AI.** Keep PR #3 Draft and do not merge or declare Phase 05 `CLOSED` until all mandatory A/B gates and actual reviewer acceptance pass.

## Latest independent gate handoff — 2026-10-24

Final source-matched implementation SHA 15f4326cd5dba898a185dd95f067969ca90aa01c, CI https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40103038011: **6/6 jobs SUCCESS**. A 75 passed/24 skipped; real isolated B 9 ingestion + 8 fault/recovery + 4 PostgreSQL + 9 Qdrant passed. SeaweedFS 4.48 is signed by the verified upstream GitHub release workflow on a pinned OCI digest; denied anonymous/wrong credentials and full S3/ClamAV container replacement have actual passing B evidence.

Engineering self-review of the application boundaries, database job leases/fencing, fail-closed antivirus, immutable quarantine and regression behavior has been recorded in phase_05_engineering_self_review.md. It is **NOT** a substitute for independent accountable review or sign-off.

**Outstanding acceptance:** An actual independent Architecture/Security reviewer must inspect current SHA and CI evidence, disposition image runtime vulnerability/license risk for synthetic CI-only use, and record a signed/attributable acceptance or change request. Complete enterprise PostgreSQL node removal/restore and On-Prem HA/DR remain Phase18 Group C, not a Phase05 technical gate. No known required scoped A/B test is left unrun before new reviewer findings.

**Do not merge or close Phase05 without human acceptance.** Technical DoD PENDING_INDEPENDENT_REVIEW; Phase05 IN_PROGRESS -> IN_PROGRESS; Production NOT_READY. P18-P05-C01–C08 remain deferred and not PASSED.
