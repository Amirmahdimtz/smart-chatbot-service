# ADR-0002: Initializing an Empty Main Branch and Phase Gates

- **Date:** 2026-10-21
- **Status:** PROPOSED — repository initialization performed, workflow approval pending

## Context and evidence

The repository API confirmed an existing public repository with push/admin permission, configured default branch `main`, **zero branches**, zero commits and size 0. Reading `README.md` returned "This repository is empty"; commit listing returned HTTP 409. There was no prior application, CI, DI, migration, dependency graph, protection setting or implementation to preserve.

## Decision

Initialize `main` with documentation-first Phase 01 and a Python-standard-library-only contract validator; do not claim an implemented FastAPI application or add Runtime dependencies. Require normal forward-only commits, review of file scope and validation results, no force-push or history rewrites. For future work prefer feature branch + PR with reviewer(s) and CI, unless the project owner specifically authorizes a direct `main` commit as for this phase. Adopt phase status/evidence tracking in [progress](../implementation/progress.md).

## Risks and approval

The repository itself is PUBLIC; do not commit credentials, customer records, internal URLs, private architecture or PII. Branch protection, CODEOWNERS, CI gate configuration and reviewer ownership need `D-18` approval. Lack of branch protection verification is not evidence that restrictions are absent. Subsequent stages must verify live branch permissions, and production data must never be placed here.

## Rollback / recovery

Because initialization creates history only, recovery is a new reverting commit, **not force push**. If a sensitive value accidentally enters Git, stop and escalate to incident response and rotate the secret; ordinary revert does not erase historical exposure.
