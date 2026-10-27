# Phase 06 — Technical Acceptance and Handoff

This is a **gate record**, not independent approval. The owner authorization is GO_FOR_PHASE06_DEVELOPMENT_ONLY. PR #4 is stacked/draft against unmerged Phase05 PR #3.

## Technical Scope and Gate

Scope requires synthetic or authorized digital PDF, genuine Persian/Arabic OCR, DOCX, FAQ and table extraction; raw versus canonical text separation, deterministic source-anchored chunks with real page/span and parser/OCR/normalizer/chunker versions, plus scoped atomic PostgreSQL persistence after genuine ClamAV clean scan.

Gate Group A: compile, import/DI, lint/format, unit/contract/negative/security/regression, dependency vulnerability/SBOM/secret scan, Docker.

Gate Group B: real OCR Persian Gold Fixture and quality, PDF and DOCX, PostgreSQL/S3/ClamAV/Worker End-to-End with persisted source-mapped chunk readback, migration upgrade/repeat/drift/test-only reverse, retry/outage/crash/lease fencing and authorization regressions. No unexecuted test is a PASS. See phase_06_evidence.md for exact SHA, runner, outcomes.

## Deferred and Outstanding

- Phase05 predecessor PR #3 remains Draft/unmerged, IMPLEMENTED_AWAITING_VERIFICATION. ADR-0008 required independent technical acceptance and synthetic CI-only OCI runtime/license residual risk disposition are not signed. Phase06 owner development approval does not change this.
- Phase06 independent technical reviewer: no attributable senior Backend/Architecture plus Security sign-off has been provided. Reviewer identity, role, date, exact tested SHA, conclusion and image/tooling risk ownership must be recorded; self-review cannot be misrepresented as independent.
- Domain/quality: small synthetic Gold Fixture does not justify corpus-wide OCR or complex PDF tables/mixed-image pages/religious/legal span quality. Scope-specific additional expert quality evidence and final D-10/D-12 thresholds remain open.
- D-07 IdP and D-08 sensitive data classification/access/retention/consent are NOT approved. No real organizational source, publication, Qdrant, embedding, Agent or LLM is authorized by Phase06.
- Group C P18-P06-C01..C06 are each DEFERRED_TO_PHASE_18, NOT_EXECUTED/NOT_PASSED, no corporate-server test requested now.
- Production Release Status: NOT_READY. Final On-Prem verification and release approval only in Phase18.

## Status Decision Rule

Maintain IN_PROGRESS while latest source-matched essential Group A/B tests are running/missing/failing. After all necessary implementation and A/B evidence are present, use IMPLEMENTED_AWAITING_VERIFICATION if technical acceptance remains pending. CLOSED — TECHNICAL ONLY is permitted only with applicable verified Technical DoD and accountable review. Do not merge/rebase PR #3 or alter older phase status solely due to this document.
