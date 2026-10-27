"""Bounded subprocess provider for document extraction; no cloud calls."""

from __future__ import annotations

import asyncio
import json
import sys

from src.core.services.persian_text.persian_processing import ExtractedPage, ProcessingRejected
from src.infrastructure.di.inject import inject
from src.infrastructure.utils.config_reader import ProcessingSettings

_SUPPORTED = {
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@inject
class DocumentExtractor:
    async def extract_async(
        self, data: bytes, mime: str, *, limits: ProcessingSettings | None = None
    ) -> list[ExtractedPage]:
        limits = limits or ProcessingSettings()
        if mime not in _SUPPORTED or not data or len(data) > limits.max_document_bytes:
            raise ProcessingRejected("unsupported_or_oversized_document")
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "src.infrastructure.providers.document.extraction_worker",
                mime,
                str(limits.max_document_bytes),
                str(limits.max_pdf_pages),
                str(limits.max_ocr_pages),
                str(limits.max_memory_mb),
                str(limits.max_cpu_seconds),
                str(limits.max_page_text_chars),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(data), timeout=limits.max_extraction_seconds)
            except (TimeoutError, asyncio.CancelledError):
                try:
                    process.kill()
                except ProcessLookupError:
                    # Child may have exited between timeout and process termination.
                    pass
                await process.wait()
                raise
            if process.returncode != 0 or len(stdout) > 8_000_000:
                raise ProcessingRejected("extraction_failed")
            decoded = json.loads(stdout)
            if not isinstance(decoded, list) or len(decoded) > limits.max_pdf_pages:
                raise ProcessingRejected("invalid_extraction")
            return [
                ExtractedPage(
                    number=item["number"],
                    text=item["text"],
                    method=item["method"],
                    engine_version=item["engine_version"],
                )
                for item in decoded
            ]
        except ProcessingRejected:
            raise
        except TimeoutError:
            raise ProcessingRejected("extraction_timeout") from None
        except asyncio.CancelledError:
            raise
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            raise ProcessingRejected("extraction_failed") from None
