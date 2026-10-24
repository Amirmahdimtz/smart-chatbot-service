"""HTTP multipart stream adapter; keeps UploadFile out of the Core domain layer."""

from __future__ import annotations

import asyncio
import hashlib

from fastapi import UploadFile

from src.core.services.ingestion.upload_validation import UploadRejected, validate_content, validate_filename


async def validate_upload_async(file: UploadFile, limit: int) -> tuple[str, bytes, str]:
    name = validate_filename(file.filename)
    if file.content_type not in {"text/plain", "application/pdf"}:
        raise UploadRejected("unsupported_format")
    extension = name.rpartition(".")[2].casefold()
    if (extension, file.content_type) not in {
        ("txt", "text/plain"),
        ("pdf", "application/pdf"),
    }:
        raise UploadRejected("content_type_mismatch")
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
        await asyncio.wait_for(asyncio.to_thread(validate_content, data, file.content_type), timeout=5)
        return name, data, hashlib.sha256(data).hexdigest()
    except TimeoutError:
        raise UploadRejected("invalid_document") from None
    finally:
        await file.close()
