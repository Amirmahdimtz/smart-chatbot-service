# ADR-0006 — Development technical closure and deferred On-Prem tests

- Date: 2026-10-24
- Status: **ACCEPTED FOR DEVELOPMENT VERIFICATION POLICY**, on the project owner's explicit instructions.
- Normative basis: owner-uploaded `Smart_Chatbot_Implementation_Plan_FA.md` **v1.1.0**, §§0.3–0.6, Phase 03, Phase 18 and Global DoD.
- Historical references: ADR-0004, ADR-0005, Phase 01–03 progress/evidence. They remain historical records; this ADR supersedes only the old **rule** treating real organizational environment testing as a prerequisite for technical phase closure.

## Decision

1. `CLOSED` for phases 01–17 means verified **technical** completion of that phase's implemented and approved scope. It does not imply production, real corporate data, HR/PII access, organizational network approval or `PRODUCTION_READY`.
2. For each phase, actual and necessary A/B tests must pass and be documented with SHA and reproducible evidence. Equivalent CI integration on real isolated PostgreSQL/Qdrant etc. is acceptable in lieu of duplicating on Windows.
3. Real organization-server testing (Group C) is **deferred to Phase 18 only** and recorded with IDs, roles, prerequisites, expected results and evidence. This is a **mandatory Release gate**, not an optional waiver.
4. A missing real dependency **essential to technical proof** (e.g. PostgreSQL for Phase 03 or stand-alone Agent test instance for Phase 15), unaddressed critical security flaw or required domain/schema/data approval still prevents technical closure of its own scope.
5. D-07 (IdP/principal) and D-08 (data classification, retention, consent, HR access) remain outstanding; structural schemas tested exclusively with synthetic records do not authorize publication, sensitive data, production migration or live APIs. The Phase 03 structural migration deliberately supports `draft/revoked` only.
6. Previously open phases are **not retroactively closed** by this ADR. Reevaluate each phase against code, test evidence and policy and record a specific technical review decision. Starting a next phase still requires owner instruction.

## Phase 03 applicability

- Phase 03 synthetic PostgreSQL structural foundation may be approved as **technical scope only** after its own current-source CI, unit/negative tests, real PostgreSQL migration (including repeated upgrade/drift/reverse on disposable DB), transaction/isolation regressions, runbook and **Phase 18 test register** are evidenced.
- Production Public/Internal physical network isolation, organization TLS/Vault/roles, WAL/PITR restore, load/HA/DR and IdP/retention policy E2E are tracked under `P18-P03-C01` through `P18-P03-C06`.
- Whether Phase 03 itself becomes `CLOSED` is decided and recorded separately after verification of those technical conditions. Neither this policy decision nor a green CI alone constitutes an organizational Security/Privacy/Release signature.
