# ADR-0001: Fixed Architecture Boundaries for Smart Chatbot

- **Date:** 2026-10-21
- **Status:** PROPOSED — awaiting Architecture/Security/Product approval
- **Context:** New, empty GitHub repository. The two project reference documents set the implementation standard and seven use cases. This ADR records the current authorized design constraints, not an implemented architecture.

## Decision

Use on-premises self-hosted Python/FastAPI modular monolith; four layers `Host → Application → Core → Infrastructure` and `Controller → Service → Repository → PsqlDbContext` for PostgreSQL. Use PostgreSQL as source of truth and Qdrant as the **only selected vector engine** (not pgvector). Preserve constructor injection, `@inject`, thin controllers, discovery naming, `BaseRepository` and Alembic patterns from the architecture guide. Use one codebase with isolated Public/Internal deployments, identities, secrets, data and retrieval boundary. Human approval required for personnel-impacting actions. External AI Agent is **unavailable** and not an implemented dependency.

## Alternatives and tradeoffs

pgvector and public Cloud inference are outside the agreed architecture; replacing them would require a separately approved ADR. Shared inference offers lower resource use but could break security isolation (`D-15`). Qdrant indexing may lag PostgreSQL; authoritative publish/revoke validation and reconciliation are therefore mandatory.

## Consequences / verification

No additional DDD/CQRS/UseCase architecture is introduced. Python Runtime, model choices, Agent API, index schemas and deployment topology are deferred to their proper phases. Approval evidence is required before this ADR is marked ACCEPTED. See [system architecture](../architecture/system_architecture.md), [deployment](../architecture/deployment_architecture.md) and [architecture contract](../architecture/architecture_contract.json).
