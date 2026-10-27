"""Bounded, conservative document preflight; no OCR or content extraction."""

from __future__ import annotations

import re
import subprocess
import sys


class UploadRejected(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def validate_filename(value: str | None) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 255
        or value.startswith(".")
        or value.strip() != value
        or not re.fullmatch(r"[\w .-]+", value, flags=re.UNICODE)
        or any(ch in value for ch in ("\u202e", "\u202d", "/", "\\"))
    ):
        raise UploadRejected("unsafe_filename")
    return value


# PDF parsing runs in a disposable child process. A 4-second deadline kills a
# stuck interpreter rather than abandoning a still-running parser thread.
# POSIX runtime memory and CPU ceilings are enforced inside that child.
_PDF_CHECK_PROGRAM = """
import sys
from io import BytesIO
try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (4, 5))
except ImportError:
    pass
from pypdf import PdfReader
payload = sys.stdin.buffer.read(5242881)
if not payload.startswith(b'%PDF-') or b'%%EOF' not in payload[-1024:]:
    raise SystemExit(1)
try:
    reader = PdfReader(BytesIO(payload), strict=True)
    valid = not reader.is_encrypted and 1 <= len(reader.pages) <= 300
except Exception:
    valid = False
raise SystemExit(0 if valid else 1)
"""


def _parse_pdf(data: bytes) -> None:
    try:
        result = subprocess.run(
            [sys.executable, "-c", _PDF_CHECK_PROGRAM],
            input=data,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise UploadRejected("invalid_document") from None
    if result.returncode != 0:
        raise UploadRejected("invalid_document")


_DOCX_CHECK_PROGRAM = """
import sys
from io import BytesIO
from zipfile import BadZipFile, ZipFile
try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (4, 5))
except ImportError:
    pass
try:
    with ZipFile(BytesIO(sys.stdin.buffer.read(5242881))) as archive:
        items = archive.infolist()
        ok = bool(items) and len(items) <= 1000 and any(
            item.filename == "word/document.xml" for item in items
        ) and sum(item.file_size for item in items) <= 24 * 1024 * 1024 and all(
            item.file_size <= 8 * 1024 * 1024
            and not (item.file_size > 0 and item.compress_size == 0)
            and not (item.compress_size and item.file_size / item.compress_size > 250)
            for item in items
        )
except (BadZipFile, ValueError, OSError):
    ok = False
raise SystemExit(0 if ok else 1)
"""


def _validate_docx(data: bytes) -> None:
    try:
        result = subprocess.run(
            [sys.executable, "-c", _DOCX_CHECK_PROGRAM],
            input=data,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise UploadRejected("invalid_document") from None
    if result.returncode:
        raise UploadRejected("invalid_document")


def validate_content(data: bytes, content_type: str) -> None:
    if not data or content_type not in {
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        raise UploadRejected("unsupported_format")
    is_zip = data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        if not is_zip:
            raise UploadRejected("invalid_document")
        _validate_docx(data)
        return
    if is_zip:
        raise UploadRejected("unsupported_archive")
    if content_type == "application/pdf":
        _parse_pdf(data)
    else:
        if data.startswith(b"%PDF-"):
            raise UploadRejected("content_type_mismatch")
        try:
            decoded = data.decode("utf-8-sig")
        except UnicodeError:
            raise UploadRejected("invalid_document") from None
        if any(ord(ch) < 32 and ch not in "\t\r\n" for ch in decoded):
            raise UploadRejected("invalid_document")
