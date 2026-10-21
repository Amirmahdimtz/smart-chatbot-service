# System Architecture — Phase 01 Proposed Contract

**Document ID:** SCB-SYSTEM-ARCH-001 · **Status:** AWAITING_APPROVAL · **Contract:** [architecture_contract.json](architecture_contract.json) · **Requirements:** [requirements_contract.json](../requirements/requirements_contract.json)

## Scope and boundaries

محصول یک Modular Monolith مبتنی بر Python/FastAPI و چهار لایه `Host → Application → Core → Infrastructure` است؛ این سند طراحی منطقی است و وجود کد Runtime را ادعا نمی‌کند. الگوی اجباری PostgreSQL برابر `Controller → Service → Repository → PsqlDbContext` است. Controller فقط HTTP/DTO، Service منطق تجاری، Repository پرس‌وجوی SQL و Providerهای Infrastructure ارتباط شبکه‌ای خارجی را مدیریت می‌کنند. وابستگی‌ها با Constructor Injection، `@inject` و discovery طبق راهنمای معماری resolve می‌شوند؛ برای CRUD از `BaseRepository` استفاده می‌شود و تغییر Model مستلزم Alembic است.

## Module ownership

| Module | Layer/Owner | Responsibility |
|---|---|---|
| Host | Host / Platform | FastAPI lifecycle, secure config, startup; Phase 02 |
| HTTP features | Application / API | Auto-discovered controllers, DTO validation, HTTP errors and routes |
| Conversation / RAG | Core / AI | Conversations, Persian query, dense+sparse retrieval strategy, fusion, reranking, source validation, abstention |
| Knowledge | Core / Knowledge | Source ingestion state, versions, approvals, publication and reconciliation |
| Religious Q&A | Core / Religious lead | Sources, legitimate differences of opinion, expert escalation (Phase 12) |
| HR matching and transfer | Core / HR | Hard eligibility, recommendations and explanations, approval gate (Phase 16) |
| Research | Core / Research office | Prior experiences, provenance and contextual difference (Phase 13) |
| Personal development | Core / Privacy owner | Consent-protected plans/progress (Phase 14) |
| Task allocation | Core / Operations | Cited tasks, capacity checks, human authorization (Phase 17) |
| SQL repositories / Qdrant / AI / future Agent | Infrastructure / Platform | All persistence, vector index I/O and network I/O; no provider built in Phase 01 |

## Online request path

`Authentication → Principal/domain/purpose → Authorization → Owned conversation → Persian normalization → Dense + Sparse/Lexical scoped retrieval → Fusion → Rerank → Metadata and publication recheck → Evidence sufficiency → Self-hosted LLM → Citation/grounding validation → Authorized persistence/response`.

Answer must abstain, ask a clarifying question or escalate when evidence is not sufficient. Retrieved text and model outputs are not commands. No prompt-based authorization. Proposed API routes in JSON contract are **candidates only**; request and error schemas, versioning, streaming protocol, idempotency and limits remain `D-16`.

## Data lifecycle

PostgreSQL is the transaction and policy source of truth for document identities, version approvals, conversation ownership, audit, and publish/revoke. Qdrant stores a rebuildable, scope-filtered retrieval index, not canonical policy state. Stable chunk/version identity, manifest, checksum and source spans support citations. Publication requires verified indexing and approval; revocation is committed in PostgreSQL before asynchronous, retryable Qdrant cleanup. Revalidation against authoritative policy blocks stale points and revocation races. Fail closed when authorized metadata cannot be reached.

Logical entities (not physical tables): conversation, message, source, document, version, chunk, index manifest, ingestion job, approved answer, citation, approval, Agent operation, audit event and consent. SQL schema, Qdrant vector dimensions and indexes are not frozen.

## Integration contract

Chatbot owns context, RAG, policy precheck, approvals and conversation. The independent AI Agent, **not yet available**, may later own specialized operations. Future integration requires a signed versioned API, identity proof, destination-side AuthZ, correlation/idempotency keys, deadlines, bounded retries, verified callback semantics where used, approval evidence and audit. There are no valid Agent endpoints today; Phase 15 handles live integration after external readiness.

## Verification and approvals

Traceability is defined in [requirements contract](../requirements/requirements_contract.json), security rules in [data access matrix](../security/data_access_matrix.md), evaluation in [evaluation plan](../evaluation/evaluation_plan.md), and open decisions in [architecture contract](architecture_contract.json). Architecture, security and domain-owner approvals have **not** been granted.
