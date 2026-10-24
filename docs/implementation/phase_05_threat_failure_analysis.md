# Phase 05 — Security and failure analysis (development-only)

| Failure / threat | Mandatory control | Observable invariant |
| --- | --- | --- |
| Client fakes principal or cross-zone/owner | existing verified JWT + Core owned-source check and fixed deployment zone | 401/403, no DB/object mutation |
| Forged filename, MIME or ZIP/polygot | conservative allowlist, size/signature/PDF parser/UTF-8 check; no archive expansion | rejected with non-sensitive code |
| ASGI/multipart allocation attack | total request cap plus upload chunk cap and bounded temporary storage | 413 with no durable accepted job |
| Malware / scanner outage | quarantine only; genuine clamd INSTREAM, fail-closed on non-OK | never awaiting approval on fault |
| Poison document or changing object | immutable reference, SHA-256 verified after GET; max attempts + dead-letter | no silent acceptance |
| Two workers claim same job | row lock SKIP LOCKED, unique lease owner and lease expiration | at most one valid owner at commit |
| Crash before/after object put | persist `staging` intent first, later CAS `queued`; stale staging observability | no unreferenced publish, operator reconciliation |
| Crash after scan before DB ACK | lease fencing + repeatable checksum/scan; retry/expire | no duplicate document version |
| DB or storage unavailable | bounded retry, no network calls in long DB transaction | durable retry/dead state |
| Log leaks metadata/content/credential | fixed error codes, sanitized audit and unexpected-exception text | no payload/key/token in API or logs |
| Accidental production enablement | explicit synthetic-only environment gate, dev/integration, deny-by-default | unavailable in staging/production |

Decisions still outstanding: D-07 IdP/permissions and D-08 real classification/retention/deletion/consent. No real-data imports, policy-dependent purge or publication while undecided. Group C organizational controls go into Phase 18 register.


## Recorded final synthetic outage controls

- Conditional S3 object creation allows byte-identical retries after lost PUT ACK but rejects overwrite of a prior different object; direct out-of-band tampering fails SHA-256 before malware approval.
- ClamAV genuine daemon EICAR and network loss/timeout are fail-closed; real docker pause drives a persistent retry_wait, followed by a real scan after unpause.
- PostgreSQL real docker pause denies a fresh application start; after unpause a new database-backed repository transaction succeeds.
- A real OS Worker was killed after PostgreSQL lease commit, and the new worker's claim/fencing prevented acknowledgement from the stale token.
- Evidence: GitHub Actions 40098823479 on 6fc7e39f39e2f5bd9ca8399ae7a03c809ae48ac0. These tests are not enterprise network, HA or backup/restore evidence, which remains deferred to Phase18.

## Updated synthetic CI storage security evidence

On SHA 15f4326cd5dba898a185dd95f067969ca90aa01c, CI https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40103038011, 9 real ingestion and 8 real outage tests PASS. Third-party Coollabs CI MinIO provider was replaced by upstream SeaweedFS 4.48, whose immutable image digest is now checked via successful keyless cosign verification of upstream GitHub release-workflow identity. Real S3 gateway denies invalid credentials/anonymous unsigned requests, conditional writes prevent overwrites, and a complete S3 container replacement preserves quarantined bytes and queued job. ClamAV container removal/recreation requires a new genuine verdict. This is not enterprise runtime vulnerability approval or HA/DR/PITR evidence. Independent accountable Security/Architecture sign-off remains NOT_SIGNED.
