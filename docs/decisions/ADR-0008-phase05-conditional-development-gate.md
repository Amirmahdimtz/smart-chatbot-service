# ADR-0008 — Phase 05 Conditional Technical Entry after Phase 04 Corrective Audit

- **Date:** 2026-10-24
- **Decision:** `CONDITIONAL_GO_FOR_DEVELOPMENT_ONLY`, **not** start, completion or production release.
- **Scope:** Phase 05 — Knowledge Source, Upload, Durable Ingestion Jobs; synthetic/disposable technical development and policy-neutral architecture only.
- **Dependencies reviewed:** Phase01/02 remain `IMPLEMENTED_AWAITING_VERIFICATION` (unchanged); Phase03 technical `CLOSED`; Phase04 corrective technical `CLOSED` after source `b5c38e8e097f53a13faf23b557c8809d3be6c063` and [PR CI 40092573876](https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40092573876) 5/5 success, including real Qdrant restore. This ADR becomes operative **only after corrective changes are merged into `main` and matching `main` CI succeeds**.
- **Authority:** AI-assisted technical entry assessment responding to owner's request; not an organizational Security, Privacy, Product or Release signature.

## Decision and bounded exception

Approve preparation and subsequent owner-directed independent **technical development only** for Phase 05 using synthetic files, isolated PostgreSQL/Qdrant/object storage/worker dependencies and known architecture-guide DI/conventions. Phase05 `NOT_STARTED` until a **separate explicit instruction from project owner** starts the work. Earlier Phase01/02 unresolved approvals are not retroactively waived; this is a limited entry exception reflecting existing tested technical foundations.

Work allowed upon explicit start: inspect and version Source/Document/Job contracts, ingestion upload validation/size/signature checks, isolated malware scanner integration, object store integrity, durable transaction/retry/lease/heartbeat/dead-letter jobs, crash recovery, worker shutdown, scoped authentication tests and synthetic E2E. Do not silently invent organizational retention, HR data classification, consent, user identity, publication or release approval; real scanning/storage/worker dependencies needed to prove Phase05 functionality must pass **actual Group A/B integration**, not only mocks.

## Hard stops

- D-07 actual IdP subject/permission binding and D-08 classification, retention, access/consent, HR publication and audit rules remain `BLOCKED_DECISION`; any **real organizational source, PII/HR dataset, external-facing upload API, permission-sensitive publication or real-data deletion/retention** requires signed applicable policy and owners before work affecting real data is performed.
- Phase05 cannot be `CLOSED` on stubs for core object storage, malware scan or durable worker recovery. Required A/B tests include negative/malicious uploads, dedup/checksum, concurrency, crash boundary, retry exhaustion and denied access. The exact technical DoD must be independently accepted.
- All true On-Prem/organization tests remain **Group C Phase18**, to be recorded with immutable new IDs when Phase05 is implemented. The policy does not permit Group C to be fabricated as PASSED.
- D-03/D-04 final embedding/sparse model policy remains open and no Phase07 index build, Phase08 retrieval or Phase09 generation starts here.
- **Phase Status:** Phase05 `NOT_STARTED`, entry permission `CONDITIONAL_GO_FOR_DEVELOPMENT_ONLY`.
- **Production Release:** `NOT_READY`; Phase18 tests and formal owner sign-offs mandatory.
