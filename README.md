# Smart Chatbot Service

Enterprise-grade, on-premises smart chatbot service for documented Persian-language knowledge retrieval and controlled organizational workflows.

**Status:** Phase 01 — IMPLEMENTED_AWAITING_VERIFICATION; owner sign-offs and workstation checks pending. No runtime application has been implemented.

## Architecture baseline

Python/FastAPI modular monolith with `Host → Application → Core → Infrastructure`, PostgreSQL as system of record, Qdrant as retrieval index, self-hosted AI inference, and strictly separated Public/Internal deployments.

## Current scope

Phase 01 captures the seven product use cases, architecture/security contracts, open decisions, verification criteria, and project progress. Runtime foundation, deployment and integrations belong to later phases. The external AI Agent is not yet available.

See `docs/implementation/progress.md` and `docs/architecture/system_architecture.md` once the Phase 01 baseline has been committed. No credentials or real organizational datasets belong in this public repository.
