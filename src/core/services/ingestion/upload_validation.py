"""Bounded, conservative document preflight; no OCR or content extraction."""

from __future__ import annotations

import asyncio
import hashlib
import re
from io import BytesIO

from fastapi import UploadFile
from pypdf import PdfReader


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


def _parse_pdf(data: bytes) -> None:
    try:
        if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
            raise ValueError("Malformed PDF")
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 300:
            raise ValueError("Unsupported PDF")
    except Exception:
        raise UploadRejected("invalid_document") from None


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


async def validate_upload_async(file: UploadFile, limit: int) -> tuple[str, bytes, str]:
    name = validate_filename(file.filename)
    if file.content_type not in {"text/plain", "application/pdf"}:
        raise UploadRejected("unsupported_format")
    content = bytearray()
    try:
        while True:
            chunk = await file.read(65536)
            if not chunk:
                break
            if len(content) + len(chunk) > limit:
                raise UploadRejected("file_too_large")
            content.extend(chunk)
        data = bytes(content)
        # PDF parser runs off the HTTP event loop, bounded by edge request size.
        await asyncio.wait_for(
            asyncio.to_thread(validate_content, data, file.content_type), timeout=5
        )
        return name, data, hashlib.sha256(data).hexdigest()
    except TimeoutError:
        raise UploadRejected("invalid_document") from None
    finally:
        await file.close()
