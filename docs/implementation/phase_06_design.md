# Phase06 — Extraction, normalization and source-mapped chunk design

**Status: IMPLEMENTED_AWAITING_VERIFICATION — DEVELOPMENT ONLY; no Phase06 technical acceptance.**
Base: Phase05 PR #3 at 26dc557fb432d8830cdb522009f795d96aabdc54. Phase06 stacked PR #4 targets unmerged Phase05 branch.
References: Implementation Plan v1.1.1, Service Architecture Guide, ADR-0008/0009/0010.

## As-is and design

Phase05 already supplies internal synthetic-only source/upload identity, immutable S3 quarantine, SHA verification, real ClamAV verdict, worker lease/heartbeat/fencing/retry/cancel and awaiting_approval. The pre-existing KnowledgeChunk has only version, ordinal, checksum and canonical_text_ref; no extraction or chunk insert. Its allowed types are TXT and PDF, with new DOCX format gated by upload validation.

Reuse rather than parallelize:

1. Existing Application upload adapter checks filename/MIME/size and bounded PDF/DOCX format preflight, then stages an immutable object and job with owner and scope. Generic ZIP and legacy binary DOC stay denied.
2. Worker claims an existing scoped job (leased + version processing), fetches from quarantine, verifies SHA256/length and obtains a true ClamAV clean verdict. **Extraction is forbidden until scan succeeds.**
3. DocumentExtractor launches a disposable Python subprocess to parse PDF/DOCX/TXT and invoke Poppler + Tesseract (fas,ara,eng) for scanned pages and mixed digital-text/raster PDF pages. No external OCR API. Parent timeout, child POSIX CPU/AS ceilings and size/page/OCR count caps; errors remain redacted codes.
4. Core processing preserves raw extractor text separately from NFC/canonical text with yeh/kaf, digit and whitespace normalization. Paragraph, heading/article, FAQ question delimiters and source-page boundaries guide chunk generation. Oversize blocks split on sentence/space when possible; fallback bounded split remains explicit behavior requiring evaluation.
5. Every chunk has deterministic UUIDv5 from document-version UUID plus processing version, truthful PDF page number or null, raw offsets and canonical checksum. Original text, canonical text, page, offset interval, section, extractor method, independently versioned normalization/chunking and actual parser or OCR runtime version (pypdf/python-docx/Tesseract/Poppler) and SHA256 are retained. Actual installed versions come from the extraction worker, not guessed in persistence.
6. IngestionRepository validates lease token/expiry, then atomically removes old chunks for that document-version+scope, inserts the complete new set and marks job completed / version awaiting_approval with audit. Failure or crash before commit cannot leave newly partial approved chunks. Stale tokens cannot persist.

## Citation and authorization

For each extracted page, offset start is inclusive and end exclusive into that exact **raw extracted page string**. These are not PDF byte positions, visual bounding boxes, PDF table row/cell coordinates or document-renderer positions. PDF page numbers are the real 1-based parser page index. DOCX/TXT has null page, never guessed pagination. Original content remains in immutable quarantined object, and original text in chunk alongside normalized canonical text. Source ID, domain, owner, classification/policy and document ID are accessible through version→document→source joins, not unaudited direct querying. No citation output, publishing, Qdrant write, Embedding or LLM is in Phase06.

Actual Word heading styles are represented as Markdown-style headings in the extracted linear transcript (the unmodified DOCX bytes remain in quarantine). DOCX table cells are transcribed in row order with a visible pipe separator, and chunk splitting prefers true row/newline boundaries over arbitrary cell cuts; genuine PDF table reconstruction is NOT claimed and is a quality-evaluation gap. Arabic alef maqsura is preserved instead of conflating it with Persian yeh in canonical text. This does not fabricate unknown source position.

## Tools and supply-chain constraints

- pypdf 6.21.2, existing BSD-3-Clause pinned dependency; no actual OCR in pypdf. Text-layout limits are documented by pypdf.
- python-docx 1.2.0, MIT, pinned for actual DOCX paragraphs/tables.
- Tesseract, Apache-2.0, local OCR with Arabic/Persian/English traineddata.
- Poppler pdftoppm for synthetic PDF rasterization; GPL/distribution obligations and packages require production packaging/security owner review. Tool/license selection is not final D-10 corpus quality acceptance.

Current defensive defaults: max 5 MiB bytes, 300 PDF pages, max 8 OCR-dependent pages per file, 768 MiB child address-space, 32s child CPU, and 38s outer extraction deadline. Adjustable chunk size 256–4000 (default 1200), overlap 0–256 subject to max 25% of chunk size (default zero). Parser limits require later measured tuning and should not be read as benchmarked capacity guarantees.

## Migration / failure semantics / roll back

Migration 0003_persian_processing only adds nullable source-text, page/span, method and processing-version columns to the existing knowledge_chunk table plus CHECK constraints. No old column/constraint is dropped; Phase05 job/approval schema stays unchanged. All migrations must be tested on disposable PostgreSQL. Test-only downgrade removes newly recorded extraction annotations; no cleanup of retained original quarantine objects or publication. Production schema deployment only in Phase18 after approved change management.

On malformed/empty/encrypted PDF, bad ZIP, OCR timeout, corrupt inputs or missing binary, fail closed: no chunk success or awaiting_approval. Retry only bounded transient classes. Existing worker remains separate from HTTP request/event loop. Existing authentication and synthetic-only deployment policy remains enforced; cross-owner/zone tests are mandatory.

## Required verification

Group A: compile, import/DI discovery, Ruff and format, unit/contract/security/negative tests, deterministic IDs, Unicode and section/table/FAQ semantics, corruption, timeout, size/page bounds, prior regressions. Group B: live synthetic digital PDF/Word/OCR Gold Fixtures with OCR CER; real scoped PostgreSQL+S3+ClamAV worker persistence; migration upgrade/repeat/drift/reverse; crash/retry/fencing and source-based readback. No skipped/unrun case may be called PASS.

Group C: P18-P06-C01 to C06 are deferred to Phase18 and are not a technical closure blocker by themselves. D-07/D-08 real-data approvals stay open. Technical status IN_PROGRESS until A/B and acceptance are proven, Production NOT_READY.

## Focused correction: resource settings, mixed PDF and disabled sources (2026-10-27)

- The existing IngestionWorkerService now passes its validated `ProcessingSettings` to `DocumentExtractor.extract_async(limits=...)`; the extraction subprocess uses those values for actual size/page/OCR/CPU/memory/time limits. Unit and real subprocess tests cover the propagation. Existing ClamAV-clean-before-parse ordering remains unchanged.
- On PDF pages containing both an extractable digital text layer and embedded raster images, the bounded OCR path is also invoked. The resulting raw extracted transcript retains the digital text and appends nonempty whole-page OCR output, using method `hybrid_pdf_ocr` and actual runtime version metadata. A real synthetic mixed-content PDF checks recovery of both sources. Page indexes and offsets remain anchored only to this generated extraction transcript, **not** visual image coordinates. OCR may duplicate digital text; do not infer perfect layout/table provenance or quality from the fixture. The OCR-page budget includes hybrid pages.
- Phase05's documented Source disable contract is preserved: disabling denies future uploads but does **not** cancel accepted queued jobs. Existing jobs can finish processing to `awaiting_approval`, never auto-publish. A real isolated integration test exercises this precise distinction; changing it to cancellation requires a separate approved policy/ADR.
- These implementation improvements do not resolve D-10/D-12 representative-corpus quality acceptance, independent review, or Phase18 organizational release gates.
