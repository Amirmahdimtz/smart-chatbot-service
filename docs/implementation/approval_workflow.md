# Phase 01 Approval and Evidence Workflow

**State:** AWAITING_APPROVAL. This document defines how to record decisions; it does not approve any contract or nominate an actual person.

The source of machine-readable approval gates is [phase_01_acceptance.json](phase_01_acceptance.json). Contracts and detailed decision owners remain in [architecture_contract.json](../architecture/architecture_contract.json) and [requirements_contract.json](../requirements/requirements_contract.json). The [progress](progress.md) status must match the machine-readable acceptance record.

## Required independent checks

| Gate | Accountable role | Minimum acceptable evidence |
|---|---|---|
| G-01 | Product Owner | Explicit scope/traceability approval, version and review date |
| G-02 | Architecture Owner | Reviewed layer/data/API/integration contracts, ADR conflicts and version |
| G-03 | Security Owner | Approved Public/Internal trust boundary and data classification, including public GitHub exposure |
| G-04 | Domain Owners | Explicit sign-off or attributable consolidated sign-off for all seven use cases, including HR/privacy |
| G-05 | Knowledge Owner | Reviewed knowledge inventory, content owner, formats, volumes, OCR samples, permitted data paths or explicitly accepted bounded deferrals |
| G-06 | Repository Admin | Verified branch protections/review policy, least-privilege writing and public repository classification |
| G-07 | Tech Lead + Product Owner | Decision register ownership, actionable milestone deadlines and documented unresolved dependencies |
| G-08 | Technical Verifier | Validation, unit and mutation-test evidence from the final proposed commit SHA |

To approve a gate, capture a review record in the repository only if its contents are safe for public disclosure. Record its relative file path in `evidence_ref`, role/accountable reviewer in `approved_by`, and ISO-8601 `approved_at`. If evidence is sensitive, store it in an approved protected location and commit a sanitized, attributable attestation (without confidential URLs, tokens or employee details), which can be linked by a relative path. No signature should be inferred from a command to continue work.

## Closing Phase 01

1. Assign actual accountable roles and approve milestone deadlines for decisions; keep unchosen models/capacity/Agent API deferred until their dependent phase.
2. Resolve or obtain approved deferrals for conflicts and document inventory. Verify all contract scopes and Public/Internal security checks.
3. Obtain attributable review evidence for **every** gate in `phase_01_acceptance.json`; align contract and per-scenario requirement statuses with these approvals.
4. Run `python scripts/validate_phase01.py`, `python -m unittest discover -s tests -v`, plus `python -O scripts/validate_phase01.py` on the proposed final source and record final SHA and results. Verify the Git diff and approval references. Never use `CLOSED` based only on unit tests.
5. Only then set `phase_status: CLOSED`, the two contract statuses to `APPROVED`, and the progress marker to `PHASE_01_COMPLETE_READY_FOR_PHASE_02`. The validator verifies structural consistency and paths, **not the authenticity of human approval**.

## Explicit non-approvals

No real Agent API, HR data classifications, SSO contract, GPU benchmark, Qdrant live deployment, model choice or HA design has been accepted here. Future milestones may remain as open decisions with identified blockers. G-05 and G-06 can be closed only with real owner acceptance of missing data/branch rules or evidence of resolution, not invented sample results.
