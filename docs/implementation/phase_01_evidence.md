# Phase 01 Evidence Ledger (2026-10-21)

## Pre-initialization observations (GitHub connector)

- Repository `Amirmahdimtz/smart-chatbot-service`: exists, PUBLIC, size=0; authenticated user `Amirmahdimtz`; push/admin/pull=true; configured default branch `main`.
- Branch search: no branches at all.
- `README.md` on `main`: HTTP 404, "This repository is empty."
- Commit listing: HTTP 409, "Git Repository is empty."
- Baseline SHA: `N/A`. No existing source/CI/DI/tests/migrations to compile or inspect.

## Scope and checks

This phase adds only README, architecture/requirements/security/evaluation/progress/decision documents and a Python-standard-library contract validator and tests. No runtime, DB migration, model, Qdrant collection or network service is created.

The validation script checks machine-readable contract structure, seven cases, unique requirement/test IDs, all trace rows, policy references, phase ownership, Agent unavailable state, open decision criteria and documentation links. Local execution must be verified separately; **no Python test pass is claimed merely because the source exists.**

## Category A (current) and evidence policy

GitHub API read/write and source inspection: **PERFORMED**. Tool-side structural validation of JSON and cross-contract invariants: performed only if reported in the commit response. Python unit/validator execution via GitHub connector: **NOT RUN** (connector offers no code execution). Git diff/content scope reviewed before GitHub tree creation; commits verified by subsequent GitHub read.


### Verified connector-side contract checks

- Command/environment: V8 tool-side verification of JSON parsed from GitHub connector contents; **not** `python`, `pytest` or service runtime execution.
- Result: **PASS**, 7 scenarios, 21 unique requirements, 21 trace rows, 9 policy IDs, 20 open decisions; 27 internal Markdown links resolved across 16 tracked files. Common credential-token pattern check flagged zero strings (not a comprehensive secret scanner).
- Commit used for persisted-content recheck: `cc5b6141bdbeb6a56a9eed9511c0447d94d52eae`; documentation baseline: `17e65367919723d91a52f5d9f8294a0c2a453c52`; initialization: `735df314b6c8dbb9322b796c7010e31fd15881d1`.
- Python validator and 6 `unittest` methods: **NOT EXECUTED** via connector; user-workstation verification still required.
- Tests on PostgreSQL, Qdrant, self-hosted models, GPU, Agent and on-prem network: **NOT EXECUTED**; not in Phase 01 runtime scope.

## Category B (workstation; execution reported by project owner)

**Evidence source:** PowerShell console transcript supplied by the project owner on 2026-10-21. This run was performed on the owner's Windows workstation, **not** directly in the GitHub connector or by ChatGPT. No personally identifying local filesystem paths are stored in this repository.

**Validated source commit:** `a6bb585d0dbed97366b9822b0d8efd30aad9ebf2` on `main`.

| Command/check | User-reported result |
|---|---|
| `git clone` followed by `git switch main` | Successful; tracking `origin/main` |
| `git rev-parse HEAD` | `a6bb585d0dbed97366b9822b0d8efd30aad9ebf2` |
| `py -3 -m py_compile scripts/validate_phase01.py tests/test_phase01_contracts.py` | No error output; next commands executed |
| `py -3 scripts/validate_phase01.py` | `PHASE_01_CONTRACT_VALIDATION_OK` with 10 linked Markdown files, 20 open decisions, 9 policies, 21 requirements and 7 scenarios |
| `py -3 -m unittest discover -s tests -v` | All six cases `ok`; `Ran 6 tests in 1.159s`; `OK` |
| `git status --short` | Empty output; clean working tree |

**Category B status: REPORTED_PASS** for Phase 01 Python syntax/contract/unittest checks and Git checkout hygiene. No user-reported errors requiring a code correction. These findings do not demonstrate runtime imports, Dependency Injection, FastAPI behavior, live database/model integrations, or independent security review.

**Remaining Phase 01 acceptance:** Architecture, Security, Product and relevant Domain Owner sign-off; traceability/policy review against real approved sources; security classification and repository governance decisions. Keep `IMPLEMENTED_AWAITING_VERIFICATION` until those evidence gates have been completed.

## Category C (on-prem future, NOT RUN)

Real PostgreSQL and Qdrant deployments, self-hosted LLM/embedding/reranker GPU/VRAM benchmarks, Persian retrieval/generation gold sets, Public/Internal isolation/SSO, load and HA/DR/restore drills, and Phase 15 live Agent E2E. Each requires approved environments, versions, source data, operators and log evidence. None may be marked passed in Phase 01.

## Rollback and incident guidance

Documentation-only change can be reverted in a new forward commit after owner review; no database/index migration exists to roll back. Never force-push. If sensitive content is leaked, initiate response and rotate immediately; reversion alone does not remove history.

## Phase 01 follow-up remediation (2026-10-21)

**Baseline:** `42480bdbb113ebeef26ff3a1fbe228ce5e106a50`. Root cause from independent audit: validation relied on `assert` (disabled by Python `-O`), required perpetual pending states and lacked an approval-evidence transition. All 20 decisions had unconfirmed role ownership and null calendar due dates; knowledge source inventory and security/repository approval had not been received.

**Changes:** Added [acceptance gate register](phase_01_acceptance.json), [approval workflow](approval_workflow.md), [knowledge inventory status](../requirements/source_inventory.md), [ADR-0003](../decisions/ADR-0003-acceptance-governance.md); converted validator checks to explicit exceptions, added negative tests, and recorded provisional milestone-based deadlines for decisions. Missing calendar deadlines and owner identities are not fabricated. No Runtime, migration, Qdrant or Agent integration implemented.

**New Python test evidence:** pending execution on final commit by owner workstation or reproducible runner. Earlier 6/6 user-reported Python test result applies only to SHA `a6bb585d0dbed97366b9822b0d8efd30aad9ebf2`. Connector-side contract/static checks must be reported separately from Python execution.

**Security and governance blockers:** Repository public disclosure review, signed architecture/product/security/domain approvals, representative knowledge inventory or signed deferred intake, and branch policy verification. Public/Internal/HR isolation remains an unimplemented Phase 02+ security control, not a tested deployment property. Phase 01 status remains `IMPLEMENTED_AWAITING_VERIFICATION`.
