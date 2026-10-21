# Smart Chatbot Service

Enterprise-grade, on-premises smart chatbot service for documented Persian-language knowledge retrieval and controlled organizational workflows.

**Status:** Phase 01 — IMPLEMENTED_AWAITING_VERIFICATION; Phase 02 — IMPLEMENTED_AWAITING_VERIFICATION (development-only foundation; SSO/on-prem/CI acceptance pending). Not production-ready.

## Architecture baseline

Python/FastAPI modular monolith with `Host → Application → Core → Infrastructure`, PostgreSQL as system of record, Qdrant as retrieval index, self-hosted AI inference, and strictly separated Public/Internal deployments.

## Current scope

Phase 01 captures the seven product use cases, architecture/security contracts, open decisions, verification criteria, and project progress. Phase 02 adds FastAPI runtime, DI/auto-discovery, JWT validation, HTTP security and observability foundation. Database, Qdrant, model and Agent integration remain future-phase dependencies. See [Phase 02 runbook](docs/operations/phase02_runbook.md). The external AI Agent is not yet available.

See `docs/implementation/progress.md` and `docs/architecture/system_architecture.md` once the Phase 01 baseline has been committed. No credentials or real organizational datasets belong in this public repository.
