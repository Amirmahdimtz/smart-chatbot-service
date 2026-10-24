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


def validate_content(data: bytes, content_type: str) -> None:
    if not data or content_type not in {"text/plain", "application/pdf"}:
        raise UploadRejected("unsupported_format")
    if data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
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
