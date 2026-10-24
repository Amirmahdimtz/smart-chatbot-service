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
