# Phase06 remediation: bounded chunk count, honest source-span audit

Date: 2026-10-27
Status: DEVELOPMENT_FIX — INDEPENDENT_REVIEW_REQUIRED
Parent: `feat/phase06-persian-processing` (Draft PR #4). This fix is staged in a separate Draft PR; no merging or prior phase closure is authorized.

## Correction to the previous audit finding

The previous claim that `group_start` and `group_end` persisted across extracted pages was **incorrect**. In the original source they are initialized **inside** `for page in pages`. Thus there was no demonstrated inter-page state leakage in Phase06. A real multi-page regression test is added to document correct page-relative offsets. The extra assignments to `group_start=None` and `group_end=0` added in Phase07's dependent branch are redundant; do not treat those assignments as proof of a fixed defect, and remove/reconcile them during branch integration.

## Actually verified code defect

In the original `IngestionRepository.finish_async`, when `success=True` but the candidate batch is missing or contains more than 4096 chunks, the method returns `False` without changing the `leased` job/version state. `IngestionWorkerService.run_once_async` ignores this boolean result and returns `True`. The lease may therefore expire and be diagnosed as `lease_expired`, obscuring the actual bounded-input failure; no document evidence is saved.

## Remediation contract

- `chunk_pages` fails with nonretriable `ProcessingRejected("too_many_chunks")` before creating the 4097th chunk. Its output remains deterministic for 4096 chunks or fewer, and source mappings are unchanged.
- `finish_async` remains defensive against invalid caller batches: an empty batch yields `empty_chunk_batch`, and a batch longer than 4096 yields `too_many_chunks`, regardless of worker version. Under a currently valid fenced PostgreSQL lease it atomically changes the job to `dead`, the DocumentVersion to `failed`, clears the lease, and commits an audit event with the true reason. The source is not published and no partial chunks are stored. Expired or stolen leases retain the original `False` fencing semantics.
- Group A tests cover exact 4096 and 4097 count, multi-page deterministic source spans; CI Group B exercises genuine isolated PostgreSQL terminal transitions, audit and zero persisted chunks for invalid batches.

## Explicit boundaries and status

This work does **not** select a real Embedding model (D-03), satisfy Phase07 publication or lift Phase05/06 specialist review requirements. No organization On-Prem Group C tests are requested: `P18-P06-C01..C06` remain `DEFERRED_TO_PHASE_18` and **NOT_RUN**. Review and CI outcomes must be recorded by exact tested source SHA.

Phase06 Technical DoD: **PENDING_REVIEW**; Phase06 existing state remains `IMPLEMENTED_AWAITING_VERIFICATION` or as separately documented by the authoritative Phase06 record (not automatically changed by this fix).
Production release status: **NOT_READY**.
