"""Phase 05 Group A: synthetic-only validation, security, DI and scanner protocol."""

from __future__ import annotations

import asyncio
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from src.core.services.ingestion.ingestion_service import IngestionService
from src.core.services.ingestion.upload_validation import (
    UploadRejected,
    validate_content,
    validate_filename,
    validate_upload_async,
)
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.models.ingestion import IngestionAuditEvent, IngestionJob
from src.infrastructure.providers.scanner.clamav_scanner import ClamAvScanner, MalwareDetected, ScanUnavailable
from src.infrastructure.providers.storage.quarantine_storage import QuarantineStorage
from src.infrastructure.repositories.ingestion.ingestion_repository import IngestionRepository
from src.infrastructure.security.token_validator import Principal
from src.infrastructure.utils.config_reader import ConfigReader, ConfigurationError


@pytest.fixture
def disabled(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.delenv("SCB_INGESTION_ENABLED", raising=False)
    yield


def test_discovery_and_model_constraints(disabled):
    container = bootstrap_di()
    assert container.resolve(ConfigReader).settings.ingestion.enabled is False
    assert isinstance(container.resolve(IngestionRepository), IngestionRepository)
    assert isinstance(container.resolve(IngestionService), IngestionService)
    assert isinstance(container.resolve(ClamAvScanner), ClamAvScanner)
    assert isinstance(container.resolve(QuarantineStorage), QuarantineStorage)
    assert IngestionJob.__tablename__ == "ingestion_job"
    assert IngestionAuditEvent.__tablename__ == "ingestion_audit_event"


def test_upload_disabled_no_public_endpoints(disabled):
    from src.host.app import create_app

    with TestClient(create_app()) as client:
        assert client.get(f"/api/v1/knowledge/jobs/{uuid4()}").status_code == 401
        assert client.post("/api/v1/knowledge/sources", json={"domain": "research"}).status_code == 401
        paths = client.app.openapi()["paths"]
        assert "/api/v1/knowledge/sources" not in paths
        assert not any("/publish" in path for path in paths)


@pytest.mark.parametrize(
    "name",
    [
        "../escape.txt",
        "/absolute.txt",
        "..\\secret.txt",
        "dir/file.txt",
        ".hidden",
        "x\n.txt",
        "evil\u202e.txt",
        "",
        " ",
    ],
)
def test_filename_rejections(name):
    with pytest.raises(UploadRejected) as exc:
        validate_filename(name)
    assert exc.value.code == "unsafe_filename"


@pytest.mark.parametrize(
    ("body", "type_", "expected"),
    [
        (b"PK\x03\x04junk", "application/pdf", "unsupported_archive"),
        (b"plain text", "application/pdf", "invalid_document"),
        (b"%PDF-malformed", "text/plain", "content_type_mismatch"),
        (b"bad\xff", "text/plain", "invalid_document"),
        (b"ok\x00bad", "text/plain", "invalid_document"),
        (b"", "text/plain", "unsupported_format"),
        (b"some text", "application/zip", "unsupported_format"),
    ],
)
def test_signature_and_corruption_rejected(body, type_, expected):
    with pytest.raises(UploadRejected) as exc:
        validate_content(body, type_)
    assert exc.value.code == expected


@pytest.mark.parametrize(
    ("name", "mime"),
    [
        ("malware.exe", "text/plain"),
        ("wrong.pdf", "text/plain"),
        ("wrong.txt", "application/pdf"),
        ("missingextension", "text/plain"),
    ],
)
def test_allowed_media_type_does_not_bypass_filename_allowlist(name, mime):
    async def exercise():
        upload = UploadFile(
            file=BytesIO(b"synthetic content"),
            filename=name,
            headers=Headers({"content-type": mime}),
        )
        with pytest.raises(UploadRejected) as exc:
            await validate_upload_async(upload, 1024)
        assert exc.value.code == "content_type_mismatch"

    asyncio.run(exercise())


def test_structurally_valid_digital_pdf_is_accepted():
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    output = BytesIO()
    writer.write(output)
    validate_content(output.getvalue(), "application/pdf")


def test_utf8_allowed():
    validate_content("سلام\nworld".encode(), "text/plain")


def test_stream_guard():
    async def exercise():
        file = UploadFile(
            file=BytesIO(b"A" * 1025), filename="sample.txt", headers=Headers({"content-type": "text/plain"})
        )
        with pytest.raises(UploadRejected) as exc:
            await validate_upload_async(file, 1024)
        assert exc.value.code == "file_too_large"

    asyncio.run(exercise())


def test_invalid_ingestion_settings_fail_closed(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.setenv("SCB_DATABASE_ENABLED", "false")
    monkeypatch.setenv("SCB_INGESTION_ENABLED", "true")
    monkeypatch.setenv("SCB_INGESTION_S3_URL", "http://remote-attacker.invalid:9000")
    monkeypatch.setenv("SCB_INGESTION_S3_ACCESS_KEY", "secret")
    monkeypatch.setenv("SCB_INGESTION_S3_SECRET_KEY", "secret")
    with pytest.raises(ConfigurationError) as e:
        bootstrap_di().resolve(ConfigReader)
    assert "secret" not in str(e.value)


def test_independent_worker_refuses_unconfigured_environment(disabled):
    from src.host.ingestion_worker import main_async

    with pytest.raises(RuntimeError, match="not enabled"):
        asyncio.run(main_async())


def test_synthetic_principal_gate(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "internal")
    config = SimpleNamespace(
        settings=SimpleNamespace(deployment_zone="internal", ingestion=SimpleNamespace(enabled=True)),
    )
    service = IngestionService.__wrapped__ if hasattr(IngestionService, "__wrapped__") else IngestionService
    obj = service.__new__(service)
    obj._settings = config.settings
    obj._security = SimpleNamespace(
        authorize=lambda p, permission: (
            None if p is not None and permission in p.permissions else (_ for _ in ()).throw(PermissionError())
        )
    )
    with pytest.raises(PermissionError):
        obj._actor(Principal("real-user", "issuer", "audience", frozenset(), frozenset({"knowledge:test:ingest"})))
    assert obj._actor(
        Principal("synthetic-test", "issuer", "audience", frozenset(), frozenset({"knowledge:test:ingest"}))
    ) == ("synthetic-test", "internal")


def test_scanner_unavailable_fails_closed(disabled):
    scanner = bootstrap_di().resolve(ClamAvScanner)
    with pytest.raises(ScanUnavailable):
        asyncio.run(scanner.scan_async(b"synthetic-document"))


def test_scanner_actual_stream_protocol_through_local_socket(disabled):
    # A protocol-only TCP test; actual malware signature integration is Group B.
    async def exercise():
        chunks = []

        async def handler(reader, writer):
            chunks.append(await reader.readexactly(10))
            length = int.from_bytes(await reader.readexactly(4), "big")
            chunks.append(await reader.readexactly(length))
            chunks.append(await reader.readexactly(4))
            writer.write(b"stream: OK\x00")
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(handler, host="127.0.0.1", port=0)
        try:
            cfg = SimpleNamespace(
                ingestion=SimpleNamespace(
                    enabled=True,
                    max_file_bytes=4096,
                    clamd_host="127.0.0.1",
                    clamd_port=server.sockets[0].getsockname()[1],
                    timeout_seconds=2,
                )
            )
            scanner = ClamAvScanner(SimpleNamespace(settings=cfg))
            await scanner.scan_async(b"test123")
            assert chunks[0] == b"zINSTREAM\x00"
            assert chunks[1] == b"test123"
            assert chunks[2] == b"\x00\x00\x00\x00"
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(exercise())


def test_scanner_malware_response_is_rejected(disabled):
    async def exercise():
        async def handler(reader, writer):
            await reader.read(1024)
            writer.write(b"stream: Eicar-Test-Signature FOUND\x00")
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        try:
            cfg = SimpleNamespace(
                ingestion=SimpleNamespace(
                    enabled=True,
                    max_file_bytes=1024,
                    clamd_host="127.0.0.1",
                    clamd_port=server.sockets[0].getsockname()[1],
                    timeout_seconds=2,
                )
            )
            with pytest.raises(MalwareDetected):
                await ClamAvScanner(SimpleNamespace(settings=cfg)).scan_async(b"synthetic")
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(exercise())


def test_scanner_timeout_without_clean_verdict_fails_closed():
    async def exercise():
        stop = asyncio.Event()

        async def daemon_without_verdict(reader, writer):
            try:
                await stop.wait()
            finally:
                writer.close()
                await writer.wait_closed()

        listener = await asyncio.start_server(daemon_without_verdict, "127.0.0.1", 0)
        try:
            cfg = SimpleNamespace(
                ingestion=SimpleNamespace(
                    enabled=True,
                    max_file_bytes=1024,
                    clamd_host="127.0.0.1",
                    clamd_port=listener.sockets[0].getsockname()[1],
                    timeout_seconds=0.05,
                )
            )
            with pytest.raises(ScanUnavailable):
                await ClamAvScanner(SimpleNamespace(settings=cfg)).scan_async(b"synthetic")
        finally:
            stop.set()
            listener.close()
            await listener.wait_closed()

    asyncio.run(exercise())
