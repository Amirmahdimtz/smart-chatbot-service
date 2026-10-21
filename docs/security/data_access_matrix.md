# Data Access and Human Approval Matrix

**Status:** PROPOSED — Awaiting Security, HR, Privacy and Content Owner sign-off. Policies `SEC-01` through `SEC-09` are machine-readable in [requirements contract](../requirements/requirements_contract.json).

| Resource / operation | Public principal | Internal employee | HR specialist with approved purpose | Expert / publisher | Human approver |
|---|---|---|---|---|---|
| Published public evidence (SEC-01/08) | Read scoped/current only | Read if allowed | Read if allowed | Review/publish if delegated | N/A |
| Internal research cases (SEC-04) | DENY | ABAC unit/purpose only | No implicit access | Research owner review | N/A |
| HR profiles and staffing (SEC-02/09) | DENY | Own data only if policy allows | ABAC + minimum required fields | No implicit access | Decision only with HR grant |
| Career/development plan (SEC-05) | DENY | Owner/consented delegates | DENY by default | Coach only if explicit delegation | No implicit access |
| Conversation and memory (SEC-03/05) | Own authorized session | Own session | No blanket access | Delegation per case | No implicit access |
| Knowledge publication/revocation (SEC-01/08) | DENY | DENY unless delegated | DENY unless delegated | Reviewer/publisher under dual control | Approve according to policy |
| Personnel changes / task execution (SEC-06/07) | DENY | No implicit execution | Propose only as authorized | DENY | Approval is necessary, not sufficient; target rechecks AuthZ |

**Mandatory gate:** deployment scope + authenticated subject + role + business purpose + classification + ownership + version/publish state + time validity; cross-tenant, cross-user or mismatched-purpose reads are denied. Where policy/identity/metadata cannot be validated, fail closed. Qdrant filters are necessary but **never sufficient**; recheck every retrieved candidate against PostgreSQL/policy state before prompting and citing.

**Classifications proposed:** PUBLIC_APPROVED, INTERNAL, RESTRICTED_HR, PERSONAL_CONFIDENTIAL, RESTRICTED_RESEARCH. These labels are **candidate classifications** until `D-08` approval; classifications for religious questions and personal attributes require explicit privacy review.

**Sensitive workflows:** HR rank/explain is advisory only. Transfers, assignments and any other high-impact writes require an authorized human decision, fresh constraint checks, destination-side AuthZ, idempotency and immutable audit chain. LLM output is never an approval token. No Agent endpoint exists.

**Safeguards:** untrusted source isolation (prompt injection); signature, MIME, size, malware and decompression checks for uploads; least-privilege credentials; minimized/redacted logs; retention, consent, export/delete as legally approved. Negative tests: public-to-HR deny, owner mismatch, revoked source, expired consent, stale approval, replayed operation, hostile retrieved text. Testing with real HR records requires authorization.

**Owners to confirm:** Security, IAM, Privacy/Legal, HR Policy Owner, Knowledge Publishing Owner. Track `D-07`, `D-08`, `D-15` and `D-19` in [architecture contract](../architecture/architecture_contract.json).
