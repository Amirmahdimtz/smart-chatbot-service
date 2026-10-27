# Phase06 — Group A/B Test Matrix and Exit Gates

Status: DEVELOPMENT ONLY. This matrix defines obligations, not their PASS status. Outcomes and exact SHA are recorded separately in phase_06_evidence.md.

| ID | Group | Requirement / scenario | Actual automated test or CI step | Acceptance |
| --- | --- | --- | --- | --- |
| P06-A01 | A | Python import/DI and compile/discovery | verify: compileall, pytest, existing DI tests | No import/resolver failures |
| P06-A02 | A | Lint/format/dependency/SBOM/secret and Docker | verify Ruff check+format, pip-audit, SBOM; docker-build; secret-scan | Each required job PASS |
| P06-A03 | A | Persian Arabic digits, kaf/yeh, NFC, mixed terms | tests/test_phase06_processing.py normalization | Ground-truth canonical matches while original preserved |
| P06-A04 | A | Structural semantic chunking and stable source spans | test_stable_chunk_ids_and_true_raw_spans; test_long_document_is_bounded_and_deterministic | Same version+input produce same UUID and true raw offsets |
| P06-A05 | A | Invalid inputs, corrupted/encrypted PDF, invalid DOCX and empty output | tests/test_phase06_processing.py malformed, empty, blank scanned | Fail closed, no fabricated page/span |
| P06-A06 | A | Parser timeout and termination | test_extractor_timeout_terminates_child | Kills child; raises controlled extraction_timeout |
| P06-A07 | A | PDF/Word document structure and table | test_real_digital_pdf_extraction_page_and_span, test_real_docx_paragraphs_and_table_extraction | Text/page/row evidence correct |
| P06-A08 | A | Regression from earlier phases | verify pytest full suite | No previously accepted phase regression |
| P06-B01 | B | Actual digital PDF extraction with pypdf | test_real_digital_pdf_extraction_page_and_span | Real page 1, text offsets, no invented metadata |
| P06-B02 | B | Actual scanned Persian PDF OCR and gold quality | test_real_scanned_persian_pdf_ocr and dedicated ingestion CI CER run | OCR binary actually invoked; CER <= 0.20 on synthetic fixture |
| P06-B03 | B | Actual DOCX table/FAQ extraction | test_real_docx_paragraphs_and_table_extraction | Document table row/content and page NULL |
| P06-B04 | B | Signed synthetic principal → S3/ClamAV → Worker → chunk persistence | test_real_digital_pdf_upload_scan_and_approval_wait | Job/version/KnowledgeChunk commit together |
| P06-B05 | B | Actual DOCX and OCR full pipeline against real services | test_real_phase06_source_storage_scanner_worker_and_chunk_spans (2 variants) | Persisted chunks exactly match extracted raw spans and stable IDs |
| P06-B06 | B | Idempotency, retry, worker crash, lease/cancel, malware and S3 outages | tests/test_phase05_integration.py and tests/test_phase05_service_outages.py | Existing negative/fencing/recovery still PASS |
| P06-B07 | B | Actual isolated PostgreSQL migration, repeat, drift, disposable reverse | postgres-integration and ingestion-integration migration CI steps | 0003 migration up/down/up works, no drift |
| P06-B08 | B | Scoped Qdrant nonregression, no Phase06 indexing | qdrant-integration | Prior Qdrant secure/provider regression PASS, no new indexing |
| P06-B09 | B | Negative cross-owner/cross-zone/source, storage integrity and malicious document | existing Phase05 integration tests + Phase06 blank/malformed tests | Deny access, no approval before scanning/chunking |

## Quality limitations requiring evidence / review

- Semantic boundaries for complex PDF tables, footnotes, religious quotes and legal numbered articles need broader authorized synthetic/domain Gold Fixtures and scored evaluation. The parser does not claim absolute PDF table layout reconstruction.
- Runtime limits (8 OCR pages, 5MiB source, 38s deadline) are initial defensive constraints and need A/B performance/quality justification; organizational capacity benchmarks are deferred to Phase18.
- Parser package source, engine version capture, binary/traineddata license/provenance and CI-only synthetic S3 OCI image residual risk must be reviewed, not silently marked approved.
- Group C controls P18-P06-C01..C06 are distinct, deferred, not PASSED. D-07/D-08 do not authorize actual data.
