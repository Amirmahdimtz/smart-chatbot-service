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
