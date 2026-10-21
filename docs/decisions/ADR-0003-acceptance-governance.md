# ADR-0003: Verifiable Phase Completion and Deferred Decisions

- **Date:** 2026-10-21
- **Status:** PROPOSED, awaiting Product / Security / Architecture approval
- **Context:** Phase 01 originally used assertions that disappear under optimized Python, expected fixed pending contract states and disallowed the completion marker unconditionally. Twenty open decisions had proposed role owners but no milestone/deadline commitments. User-reported workstation tests verified only the earlier source commit.

## Decision

Provide a Python-standard-library, optimization-safe validator with explicit exceptions, duplicate/traceability checks and approval-state consistency. Introduce a separate [acceptance register](../implementation/phase_01_acceptance.json) and an [approval process](../implementation/approval_workflow.md). Require approval evidence and attributable reviewer metadata before an acceptance gate is structurally eligible to close. Use target **phase gate milestones**, not made-up calendar dates, to make deferred decisions actionable; keep actual calendar due dates and owner confirmations open until provided. Successful tests do not count as security or domain sign-off.

## Security and scope constraints

The repository is public; store only sanitized review attestations and non-sensitive paths. Do not create HR data, fake Agent endpoints, Qdrant instances, Runtime services or phases beyond 01. Repository governance and real source inventory are separate acceptance gates. Change the completion marker only when approved contracts, all gate evidence and necessary phase checks are consistent. The validator verifies consistency and local file existence, not signer identity or approval authenticity.

## Alternatives / consequences

Implicit approval, an always-passing `assert` check, and inventing calendar deadlines were rejected. Deferring choices until responsible experts confirm them preserves sound engineering constraints while documenting their dependency milestones. Phase 01 remains `IMPLEMENTED_AWAITING_VERIFICATION` until all accountable reviews have genuinely occurred.
