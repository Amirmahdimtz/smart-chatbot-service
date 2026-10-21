# Development, Review and Verification Workflow

1. At each phase start read both current reference documents and ADRs, check live GitHub `main`, its SHA/tree, permission and phase progress. Do not assume files/branches/classes exist.
2. Record scope, data/API/security impact, approval requirements and rollback before changes. Normal work uses issue/branch/PR, reviewer sign-off and checks; direct `main` commit is permitted here by explicit owner instruction. Final branch-protection/reviewer policy awaits `D-18`.
3. Apply minimal file changes; maintain the four-layer/DI/discovery naming conventions, real providers only, no fake production implementations. Schema change requires Alembic metadata/migration and recovery evidence; index change requires version/rebuild plan.
4. Run syntax, lint, contracts, unit/integration, security/negative tests **that are actually available**, and report exact commands, environment, outcomes and skipped checks. Review diff and avoid secrets/PII. No Unit/Compile assertion for Phase 01 empty-runtime baseline.
5. Record `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED_AWAITING_VERIFICATION`, `CLOSED`, `BLOCKED_EXTERNAL`, `BLOCKED_DECISION` or `FAILED_VERIFICATION` against each phase; close only on evidence and owner approval. `PHASE_01_COMPLETE_READY_FOR_PHASE_02` is forbidden until full DoD signed off.
6. Validate phase 01 documentation without dependencies: `python scripts/validate_phase01.py`, `python -m unittest discover -s tests -v`. CI integration belongs to Phase 02, pending branch/CI decisions.
7. Capture logs scrubbed of secrets/HR/PII; evidence references may include commit SHA, signed owner decision, test transcripts and benchmark versions. Store protected operational evidence outside public Git where required.

## Cross-environment test partition

**A / connector + local code:** JSON contracts, trace references, documentation paths, baseline source inspection, and diff/secret review. **B / user workstation:** clone/pull, Python stdlib validator/unit tests; no service runtime dependencies yet. **C / on-prem future:** real LLM/embedding/reranker GPU and Persian benchmark, Qdrant/PG services, isolation, load, restore/HA, external Agent E2E. No category-C evidence has yet been produced.

See [progress](progress.md) and [evaluation plan](../evaluation/evaluation_plan.md).
