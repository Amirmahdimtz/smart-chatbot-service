# ADR-0010 — Phase06 dependent branch and synthetic-only development authorization

- Date: 2026-10-27
- Status: ACCEPTED FOR DEVELOPMENT ONLY (explicit project-owner instruction)
- Authority: Project owner; **not** independent technical/security acceptance.
- Scope: PHASE_06 — Persian NLP, Document Extraction, OCR and Semantic Chunking.
- Reference: Implementation Plan v1.1.1 §§0.2–0.6, Phase05, Phase06, Phase07, Phase18 and Global DoD; Service Architecture Guide; ADR-0008/0009.

## Observed repository state at authorization

- Repository: Amirmahdimtz/smart-chatbot-service; main at 0c817b1886b1668576e2037394f4b2d5cbf4997b.
- Phase05 PR #3 is OPEN/DRAFT, unmerged; source HEAD 26dc557fb432d8830cdb522009f795d96aabdc54.
- Its latest source-matched CI 40464098716 completed SUCCESS. No submitted PR reviewer approval was found when Phase06 began. ADR-0008 independent acceptance and synthetic CI-only container runtime/license residual-risk decision remain outstanding.
- Phase05 is IMPLEMENTED_AWAITING_VERIFICATION, **not CLOSED**. D-07/D-08 real-data policy is unresolved.
- Base Phase06 branch on the exact Phase05 HEAD; create stacked PR #4 into feat/phase05-ingestion, not main. PR #3 must not be merged, rebased, closed or marked accepted by Phase06 engineering.

## Decision

Allow implementing independently verifiable Phase06 code, isolated synthetic extraction/OCR, additive migration, test fixtures and documentation, without altering prior-phase status or production policy.

**Integration placement:** Existing QuarantineStorage → SHA verification → ClamAvScanner → DocumentExtractor (isolated child) → Persian normalization/semantic chunking → one PostgreSQL transaction persisting KnowledgeChunk plus completed job / awaiting_approval version. On parser failure, do not commit any chunks and do not transition to awaiting_approval. ClamAV fail-closed is preserved. No HTTP event-loop parsing or cloud OCR.

**Tooling choice for synthetic engineering evaluation:** current pinned pypdf (BSD-3-Clause) for PDF text; python-docx 1.2.0 (MIT) for DOCX; Tesseract with fas/ara/eng (Apache-2.0) and Poppler pdftoppm for raster OCR. All must run on isolated synthetic fixtures. Poppler packaging, binary license obligations, language-data quality and runtime images require separate distribution/security review before any production packaging/acceptance. Neither tool selection nor local OCR constitutes D-10 benchmark closure on organization corpus.

**Traceability:** Per-chunk positions refer to *actual extracted page text*, not PDF byte coordinates or a conjectured bounding box. OCR page number comes from the parser's page index; DOCX page remains null. Preserve verbatim extracted text and canonical search text in distinct columns. Include extractor method and processing version.

## Hard stops / no automatic closure

- Full Phase06 technical DoD needs source-matched A/B results: real OCR and parser, isolated PostgreSQL+S3+ClamAV+worker+chunk persistence, migration/drift, retries and negative security regressions, evaluation and independent review if required.
- No real organizational source, no unauthorized HR/PII, no publication, Qdrant index/embedding, retrieval, Agent, or LLM.
- Group C only Phase18 with IDs P18-P06-C01..C06, all deferred; no server test requested now.
- Phase06 remains IN_PROGRESS until Technical DoD verified. Production Release Status NOT_READY.
