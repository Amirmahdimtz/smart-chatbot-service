# Phase07 — Group A/B Test Matrix (kickoff)

| ID | Group | Scenario | Test/Evidence | Status |
| --- | --- | --- | --- | --- |
| P07-A01 | A | Source checksum, IDs, ordinals, deterministic manifest | tests/test_phase07_indexing.py | EXECUTED_ONLY_IF_CI_CONFIRMED |
| P07-A02 | A | Invalid dimension, count, nonfinite and zero cosine | tests/test_phase07_indexing.py | EXECUTED_ONLY_IF_CI_CONFIRMED |
| P07-A03 | A | Phase06 multiple PDF pages with true raw spans | tests/test_phase06_processing.py::test_multipage_chunks_never_reuse_previous_page_offsets | EXECUTED_ONLY_IF_CI_CONFIRMED |
| P07-A04 | A | No publish, out-of-zone staging and bounded batch | tests/test_phase07_indexing.py | EXECUTED_ONLY_IF_CI_CONFIRMED |
| P07-B01 | B | Actual authenticated Qdrant unpublished stage, replay, deny visible query | tests/test_phase07_qdrant.py (CI Qdrant job) | EXECUTED_ONLY_IF_CI_CONFIRMED |
| P07-B02 | B | Two actual multilingual/Persian model benchmarks incl license/Recall/RAM/latency | model selection + signed D-03 decision | REQUIRED_NOT_RUN |
| P07-B03 | B | Actual embedding provider finite/dimension batch output, warm model | real pinned runtime + synthetic text | REQUIRED_NOT_RUN |
| P07-B04 | B | Durable PG manifest/index jobs/retries/lease/restart | real PG/Qdrant integration | REQUIRED_NOT_RUN |
| P07-B05 | B | Alias reindex/cutover/rollback, model revision change | real Qdrant and approved D-03 | REQUIRED_NOT_RUN |
| P07-B06 | B | Publish/revoke race, denied stale vectors, no stale citations | real PG/Qdrant with permitted synthetic identities | REQUIRED_NOT_RUN |
| P07-B07 | B | Qdrant outage/partial upsert/drift reconciliation | isolated fault injection and manifest checksum readback | REQUIRED_NOT_RUN |
| P07-B08 | B | Sparse/hybrid selection and benchmark | genuine candidate/Gold dataset D-04 | REQUIRED_NOT_RUN |

Group C IDs P18-P07-C01..C07 are separately recorded for Phase18 and NOT_RUN. Full Phase07 Technical DoD is NOT satisfied by tests in the initial slice.
