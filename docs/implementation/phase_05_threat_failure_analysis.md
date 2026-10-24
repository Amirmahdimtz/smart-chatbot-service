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
