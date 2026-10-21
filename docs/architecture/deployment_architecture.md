# On-Premises Deployment Architecture — Phase 01 Proposal

**Status:** AWAITING_APPROVAL · No server count, deployment artifact or runtime has been verified. See [architecture contract](architecture_contract.json) and [security matrix](../security/data_access_matrix.md).

## Logical topology

`Public Client → Public Edge/WAF → Public API/Policy → Public RAG → Public Qdrant + PostgreSQL + Approved Public Inference`

`Internal Client → Internal Gateway/IdP → Internal API/Policy → Internal RAG → Internal Qdrant + PostgreSQL + Private Inference`

`Approved internal source → Quarantined ingestion/worker → Review/Publish → Internal knowledge`. A separate explicit controlled publication process is needed to move approved knowledge to Public; synchronizing internal data wholesale is forbidden. `Internal API → future secured Agent boundary` is a dependency, not an existing service.

Both deployments share **source code only**. They require separate network trust zones, credentials, secret stores/scopes, data services, backups and audit access. Public must not route to Internal HR/Agent/data. Inference resources cannot be shared across scopes without memory/request isolation evidence and security approval (`D-15`). Worker isolation and queued ingestion must not block online requests; broker selection `D-11` remains open.

## Trust/security

- Clients and external documents are untrusted. TLS at edges and mutually authenticated internal service transport as applicable; denied-by-default firewall rules and egress policy.
- Approved IdP/SSO and actual claims/permissions pending `D-07` and `D-08`. Server-side RBAC+ABAC and per-request principal/purpose are mandatory.
- Secrets/certificates in an approved internal secret manager; never committed. Rotate and audit credential usage. Public/Internal audit streams remain separately controlled.
- PostgreSQL is never internet-accessible; Qdrant never exposed to browsers. Encryption in transit/at rest, least-privilege DB and Qdrant credentials, ingress limits and tamper-resistant audit are required design gates.

## Backup, reliability and recovery

Backup scope: PostgreSQL base backup + WAL/PITR; Qdrant node snapshots and alias/schema metadata; source object storage; cryptographic keys/config metadata; approved model/prompt versions. Restore must revalidate document/version/retrieval manifest, policy and citations; stale Qdrant points must not become published after a restore. Queue/worker jobs need durable idempotent recovery, bounded retry and a reconciliation procedure.

HA topology and replication/failover remain `D-05`; availability/SLO and recovery targets remain `D-12`/`D-20`; GPU/VRAM capacity remains `D-13`. A single GPU inference path is a SPOF. No proof of failover or restore exists in Phase 01; drills belong to dependent phases and Phase 18.

## Operational zones and acceptance evidence

The stages development, integration, staging and production require independent credentials/data scopes; **no unapproved staff/HR data** in development or tests. Future evidence: firewall policy and deny probes, service-identity verification, TLS/cert rotation, secret scans, network path tests, encrypted backup manifests, PITR/Qdrant restore transcripts, version-aligned source citations, cross-zone exfiltration negatives, load/HA reports and owner signoffs.
