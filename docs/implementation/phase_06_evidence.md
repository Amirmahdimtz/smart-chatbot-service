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
