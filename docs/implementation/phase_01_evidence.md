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

## Category B (workstation)

Run `python scripts/validate_phase01.py` and `python -m unittest discover -s tests -v` from repository root; send sanitized terminal transcript and `git rev-parse HEAD`. Exact OS instructions provided separately to project owner.

## Category C (on-prem future, NOT RUN)

Real PostgreSQL and Qdrant deployments, self-hosted LLM/embedding/reranker GPU/VRAM benchmarks, Persian retrieval/generation gold sets, Public/Internal isolation/SSO, load and HA/DR/restore drills, and Phase 15 live Agent E2E. Each requires approved environments, versions, source data, operators and log evidence. None may be marked passed in Phase 01.

## Rollback and incident guidance

Documentation-only change can be reverted in a new forward commit after owner review; no database/index migration exists to roll back. Never force-push. If sensitive content is leaked, initiate response and rotate immediately; reversion alone does not remove history.
