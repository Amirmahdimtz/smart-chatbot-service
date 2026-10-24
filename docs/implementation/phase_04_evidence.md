# Phase 04 — Evidence and verification log

**Baseline main:** `0b34f457bacfe4aba704ff01563fcd1c4e62a97c`, CI [40088833699](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40088833699) successful before Qdrant changes.
**Implementation:** `feat/phase04-qdrant`, [PR #1](https://github.com/Amirmahdimtz/smart-chatbot-service/pull/1).
**Technology:** Qdrant Server 1.20.0 and client 1.20.0.

## Historical first CI (DO NOT mark pass)

Commit `bac41b172c32e1b76c68ff377274b1d17124eed0`, [Actions 40089879822](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40089879822).

- `docker-build`: SUCCESS, including production image build.
- `verify`: FAIL (41 passed, 3 skipped, 1 failed): Phase 02 regression expected exactly 8 DI providers; new legitimate Qdrant provider increases count to 9.
- `qdrant-integration`: FAIL (4 passed, 1 failed); negative-credential test incorrectly treated SDK `AsyncQdrantClient` as an async context manager; server startup and authenticated health probe worked.
- `secret-scan`: FAIL **before scan**, because PR event now requires explicit `GITHUB_TOKEN` for `gitleaks-action`. This is **NOT** a vulnerability finding and **NOT** a passed scan.
- `postgres-integration`: see linked job result; not inferred from other jobs.

Root causes fixed in follow-up commit `04c806ec1c24987efe0260da737e9f334819ab82` (accurate DI count, explicit SDK close, action token, strict publication boolean). New CI evidence must be verified independently. This document must not be treated as evidence of technical closure.

## Tests A Executed + Actual Results

First CI failure above. Retest results are not yet documented here. Requirements: import/compile, Phase 01 validator, Phase 01–03 regressions, Ruff check/format, pip-audit strict, SBOM, Docker build, gitleaks, contract and negative tests, timeout/retry/DI.

## Tests B Executed + Actual Results

The first real CI Qdrant v1.20.0 service was provisioned with a disposable test API key and authentic collection health probe succeeded, but the integration test aborted before collection scenarios. End-to-end tests for collection, filtering, aliases, snapshot, recovery and incompatible schemas require complete repeat evidence from a later job.

## Tests A/B Required but Missing

As of this log version: green full PR CI, verified actual Qdrant operations, restore/rebuild drill, security/negative regression, re-run audit, CI evidence on final SHA. No Group C substitute is claimed.

## Tests C Deferred to Phase 18

`P18-P04-C01` – `P18-P04-C10` are recorded in [Phase 18 Register](phase_18_verification_register.md), all `DEFERRED_TO_PHASE_18`. No organization test has been run.

## Decision

**Technical DoD:** NOT YET VERIFIED. **Phase Status Before:** NOT_STARTED. **Current:** IN_PROGRESS. **Phase Status After:** not CLOSED. **Production Release:** NOT_READY. Review evidence after the next CI before changing status.
