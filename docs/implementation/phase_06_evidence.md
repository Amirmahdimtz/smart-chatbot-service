# Phase06 — Technical A/B Evidence and Open Gates (2026-10-27)

**Authorization:** GO_FOR_PHASE06_DEVELOPMENT_ONLY. GitHub Amirmahdimtz/smart-chatbot-service, Phase06 stacked Draft PR #4 into Phase05 Draft PR #3 (not merged). Code tested on commit 1f692a65d16a3ad8add702e0f2d262fb276aee0b (following source/CI commits add evidence-only docs; reverify head before acceptance). Full run https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40469093209 .

## Actual source-matched GitHub CI evidence

Environment: GitHub Actions ubuntu-latest, Python 3.12 with pinned requirements-dev.txt and requirements.txt, actual disposable PostgreSQL 16, authenticated Qdrant 1.20, isolated S3-compatible quarantine and true ClamAV; actual Poppler 24.02.0, Tesseract 5.3.4 with Persian/Arabic/English OCR models. Synthetic inputs and principals only.

CI run 40469093209 on above exact SHA: **6/6 jobs SUCCESS**: verify, docker-build, secret-scan, postgres-integration, qdrant-integration and ingestion-integration. This success is observed, not inferred.

### Tests A Executed + Actual Results

- verify: python -m compileall -q src scripts tests: PASS
- python scripts/validate_phase01.py and python -O scripts/validate_phase01.py: PASS
- python -m pytest -q: **88 PASSED / 27 SKIPPED**, 1 warning. SKIPPED tests are not PASSED; isolated service-dependent tests are exercised by dedicated CI integration jobs.
- ruff check src tests and ruff format --check src tests: PASS.
- pip-audit -r requirements.txt --strict: PASS on inspected source-SHA dependencies.
- cyclonedx-py environment --output-format JSON --output-file sbom.json: PASS / SBOM artifact generated.
- docker build and non-root image inspection: PASS (runtime bundled self-hosted OCR).
- gitleaks secret scan job: PASS.

### Tests B Executed + Actual Results

- In the real disposable ingestion-integration job: python src/infrastructure/scripts/run_migrations.py --upgrade (twice); --check; --downgrade-test-only; --upgrade; --check: PASS on its isolated PostgreSQL schema, including additive 0003 version/mapping columns and drift test.
- python -m pytest -q tests/test_phase05_integration.py: **12 PASSED**, including new actual source API→S3→ClamAV→independent-worker→atomic PostgreSQL Chunk persisted readback for digital PDF, DOCX (table and FAQ) and scanned Persian PDF. Source page/raw span and deterministic identity actually compared after persistence; no Qdrant write/publish.
- python -m pytest -q -s tests/test_phase06_processing.py::test_real_scanned_persian_pdf_ocr: **1 PASSED**. Actual synthetic Gold Fixture expected Persian text was "سلام دنیا"; measured and printed CER **0.000**, genuine Tesseract 5.3.4 and Poppler 24.02.0.
- python -m pytest -q tests/test_phase05_service_outages.py: **8 PASSED**, actual reversible and full service outage/recovery tests on disposable CI dependencies.
- postgres-integration python -m pytest -q tests/test_phase03_postgresql.py: **4 PASSED**; migration checks/reverse/reupgrade PASS.
- qdrant-integration python -m pytest -q tests/test_phase04_qdrant.py: **9 PASSED** with real Qdrant in isolated CI.
- Negative tests include blank scanned PDF reject, malformed DOCX/PDF reject, timed-out parser child killed, scoped auth denied, malware fail-closed and recovery. No real corporate data used.

**A/B quality interpretation:** CER=0.000 is one intentionally clean synthetic text sample, not corpus-wide OCR precision. Parser/normalization/chunker versions, layout semantics and source offsets are traceable but untrusted PDF tables cannot be assumed structurally correct. Real-domain test-corpus thresholds D-10/D-12 and final packaging provenance require additional technical evidence/review before broader quality claims.

## Tests A/B Required but Missing / Review Items

- Exact latest documentation/Source SHA may be ahead of recorded implementation CI; update test evidence to latest SHA when final CI completes.
- Scope-specific wider Gold Fixtures for mixed scanned/digital PDF, difficult RTL tables, law articles and religious quotation continuity, and measured quality thresholds beyond the simple synthetic fixture.
- Independent attributable architecture/security review and actual residual risk disposition of synthetic CI-only SeaweedFS OCI runtime/license/vulnerability risk inherited from Phase05 ADR-0008. Owner permission to develop is not an independent reviewer signature.
- No known failures among the test cases in run 40469093209. The earlier failed code SHA 14d3798529b049f488b5003ad2a47559e0eda5f0 had a Ruff format failure and wrongly blank "digital PDF" positive fixture; these were fixed before the passing run. Skips remain reported.

## Tests C Deferred to Phase18 / Register IDs

P18-P06-C01, P18-P06-C02, P18-P06-C03, P18-P06-C04, P18-P06-C05, P18-P06-C06: each DEFERRED_TO_PHASE_18, NOT_RUN. Covers On-Prem OCR runtime/hardware, IdP/Vault policy, Public/Internal network, HA/DR/restore, corporate load/stress/soak and security/UAT. These are not Phase06 development closure gates by themselves.

## Decisions / Production

Technical DoD: Engineering core implemented and source-specific initial A/B evidenced, but broader quality/independent technical review and latest source-SHA verification remain open. Phase06 cannot be reported CLOSED on this evidence alone. Phase05 remains IMPLEMENTED_AWAITING_VERIFICATION. No PR merge, real-data approval, Qdrant/embedding, publication or corporate-server test performed. Production Release Status: NOT_READY.


## Updated complete implementation A/B verification — 2026-10-27

**Exact fully tested implementation SHA:** 289f216ca4f6e77d30211064e6bb0202ad2fd182
**CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40470440670

All **6/6 CI jobs SUCCESS** on that exact implementation source. This supersedes the earlier 1f692a65 implementation results for scoped engineering. The code at this SHA includes the final source/normalizer/engine version metadata, explicit YAML configuration, Arabic-sensitive normalization, real DOCX Heading extraction, anti-malware first ordering, true PDF/DOCX/OCR persistence and encrypted-PDF negative test.

**Tests A Executed + Actual Results:**
- Python compile, DI/import/contract, Ruff check and format, Pydantic/config and full security/negative/regression: **90 PASSED, 27 SKIPPED**, one warning. Skips are not PASS.
- strict pip-audit, SBOM, Docker image build/non-root validation, secret scan: SUCCESS in their respective jobs.

**Tests B Executed + Actual Results:**
- Actual PostgreSQL additive 0003 migration upgrade/repeat/drift, disposable reverse/upgrade: SUCCESS.
- Actual scoped synthetic upload → immutable S3 → ClamAV → separate Worker → Chunk PostgreSQL atomic persistence for digital PDF, DOCX with heading/FAQ/table, and scanned Persian PDF: **12 PASSED**.
- Genuine Poppler/Tesseract synthetic Gold Fixture run with real OCR: **2 PASSED** (Persian expected "سلام دنیا", Arabic expected "مرحبا بالعالم"). Measured CER **0.000 for Persian** and **0.000 for Arabic** for these *two synthetic fixtures only*. Actual binaries: Tesseract 5.3.4, Poppler 24.02.0.
- Actual reversible and full stop/recovery of isolated dependencies: **8 PASSED**.
- Real PostgreSQL regression **4 PASSED**; real Qdrant regression **9 PASSED**.
- The new encrypted PDF is rejected at both upload and extraction boundaries; empty scanned PDF, malformed DOCX/PDF, expiry and timeout/cancellation tests execute within required synthetic test suite.

**Tests A/B Required but Missing:** Independent accountable technical review/signoff of final Phase06 engineering and scoped security/licensing/quality decisions; representative Gold Fixtures and acceptance criteria for difficult PDF layout, longer scanned documents, sensitive Arabic/legal/religious structure, mixed digital+image PDFs. If their absence is determined essential for technical DoD, Phase06 cannot be CLOSED. Do not treat small zero-CER samples as general OCR quality evidence. Post-implementation documentation commits do not change tested behavior, but the final branch-head CI should be verified before status decisions.

**Tests C Deferred:** P18-P06-C01 through C06, DEFERRED_TO_PHASE_18, NOT_EXECUTED. Prior Phase05 P18-P05-C01..C08 remain deferred.
**Technical DoD:** ENGINEERING_AB_VERIFIED — ACCEPTANCE_PENDING.
**Phase status handoff:** NOT_STARTED → IMPLEMENTED_AWAITING_VERIFICATION (development work finished but independent quality/security review pending), subject to latest GitHub PR head verification.
**Production Release Status:** NOT_READY. PR#3 and PR#4 must remain Draft and unmerged without explicit reviewer/owner decisions.


## Focused remediation and exact-source CI verification — 2026-10-27

**Code SHA:** `730a04d807f2ced5a5ac61696cb97704a1886101` (subsequent evidence/documentation commits must be checked separately).
**Actual completed CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40475859190 — **6/6 jobs SUCCESS**: verify, ingestion-integration, postgres-integration, qdrant-integration, docker-build, secret-scan.

**Scope corrected (without affecting Phase05 status or merging PRs):**
1. `IngestionWorkerService` now passes the validated `ProcessingSettings` to the real `DocumentExtractor`; a new unit test checks the exact Worker → scan → extract ordering and config identity, and a genuine two-page PDF subprocess test proves the configured page cap is enforced.
2. The parser runs bounded local OCR on PDF pages with raster images even when digital text is extractable. The `hybrid_pdf_ocr` raw transcript retains the digital layer and recognized image text; real synthetic mixed-PDF OCR, true page index, runtime version and truthful raw offsets are covered. Potential text duplication, decorative image OCR and complex layout quality still require broader Gold Fixtures/review.
3. Phase05 `disable_source` semantics were confirmed rather than changed: no new uploads, while previously accepted jobs may complete to `awaiting_approval` without publication. A new real authenticated PostgreSQL/S3/ClamAV/Worker integration test verifies this.
4. An intermediate source CI run https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40475287944 had **5/6 jobs SUCCESS**, with **2 failures / 6 passes** in the real service-outage test group caused by `StorageUnavailable` on S3 PUT immediately after CI-only service recreation. The failure is retained here, **not erased or claimed PASS**. The test now requires a genuinely successful immutable S3 PUT with bounded retry (max 25 attempts) before independent ClamAV/PostgreSQL cold restart exercises; persistent unavailability still fails the test.

**Tests A Executed + Actual Results** (CI above, Python 3.12 on GitHub ubuntu runner): compile/import and contracts successful, Ruff check/format successful, general pytest **93 PASSED / 28 SKIPPED / 2 warnings**, strict pip-audit `No known vulnerabilities found`, Docker build, SBOM and secret scan jobs SUCCESS. Skipped tests are not PASS.

**Tests B Executed + Actual Results** (real isolated synthetic integrations in the above CI):
- Actual PostgreSQL/S3/ClamAV/independent Worker ingestion, DOCX/PDF/chunk persistence, Source-disable policy: **13 PASSED / 1 warning**.
- Real Tesseract and Poppler Persian and Arabic scanned-PDF Gold Fixtures: **2 PASSED**, each synthetic CER=0.000; this is **not** a corpus-wide quality claim.
- Actual Docker fault injection, restart/recovery, lease and storage/scanner cases: **8 PASSED**.
- Real PostgreSQL regression: **4 PASSED**; real Qdrant regression: **9 PASSED**.
- Migration/check/reverse/reupgrade checks are covered by the successful isolated jobs.

**Tests A/B Required but Missing / Review:** representative mixed Persian/Arabic scanned corpora (beyond clean synthetic fixtures), complex PDF tables/reading order, religious/legal quote continuity, quality criteria D-10/D-12; attributable independent Architecture/Security technical review and scoped OCR/OCI license and runtime-risk disposition. The corrected test failures do **not** waive these technical acceptance requirements.

**Tests C Deferred to Phase18:** P18-P06-C01 through P18-P06-C06 are `DEFERRED_TO_PHASE_18`, NOT_RUN, NOT_PASSED. Phase05 deferred IDs remain unchanged.

**Technical DoD Status:** `ENGINEERING_AB_VERIFIED — ACCEPTANCE_PENDING`.
**Phase Status Before / After this remediation:** `IMPLEMENTED_AWAITING_VERIFICATION → IMPLEMENTED_AWAITING_VERIFICATION`.
**Production Release Status:** `NOT_READY`. PR #3/#4 still Draft/unmerged; no organizational server access, real corporate data, publication, Qdrant indexing or model serving approved or performed.
