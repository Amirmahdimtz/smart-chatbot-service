"""Isolated, resource-bounded extractor process. Never invoke on unscanned input.

Called only by DocumentExtractor after the existing ClamAV gate. Its stdout is
protocol JSON, never application logging. Original file bytes remain immutable.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib.metadata import version
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader

_MAX_BYTES = 5_242_880
_MAX_PAGES = 300
_MAX_OCR_PAGES = 8
_MAX_TEXT_PER_PAGE = 4_000_000
_WORD_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _limits(memory_mb: int, cpu_seconds: int) -> None:
    if os.name == "posix":
        import resource

        memory_bytes = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 2))


def _docx_zip_guard(data: bytes) -> None:
    try:
        with ZipFile(BytesIO(data)) as archive:
            items = archive.infolist()
            if (
                len(items) > 1000
                or not any(i.filename == "word/document.xml" for i in items)
                or sum(i.file_size for i in items) > 24 * 1024 * 1024
                or any(
                    i.file_size > 8 * 1024 * 1024
                    or (i.file_size > 0 and i.compress_size == 0)
                    or (i.compress_size > 0 and i.file_size / i.compress_size > 250)
                    for i in items
                )
            ):
                raise ValueError("invalid_document")
    except (BadZipFile, OSError, ValueError):
        raise ValueError("invalid_document") from None


def _docx(data: bytes) -> list[dict]:
    from docx import Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    _docx_zip_guard(data)
    document = Document(BytesIO(data))
    sections = []
    for item in document.element.body.iterchildren():
        if isinstance(item, CT_P):
            paragraph = Paragraph(item, document._body)
            text = paragraph.text.strip()
            style = paragraph.style.name if paragraph.style is not None else ""
            if text and style.startswith("Heading "):
                level = style.removeprefix("Heading ")
                if level.isdigit() and 1 <= int(level) <= 6:
                    # Mark real OOXML heading semantics in the linear transcript;
                    # the source remains the original immutable DOCX object.
                    text = "#" * int(level) + " " + text
        elif isinstance(item, CT_Tbl):
            table = Table(item, document._body)
            text = "\n".join(
                " | ".join(cell.text.replace("\n", " ").strip() for cell in row.cells) for row in table.rows
            )
        else:
            continue
        if text:
            sections.append(text)
    text = "\n\n".join(sections)
    return [{"number": None, "text": text, "method": "docx", "engine_version": "python-docx/" + version("python-docx")}]


def _ocr_pdf_page(data: bytes, number: int, max_page_text_chars: int) -> str:
    rendered = subprocess.run(
        ["pdftoppm", "-f", str(number), "-l", str(number), "-scale-to", "1500", "-gray", "-png", "-singlefile", "-"],
        input=data,
        capture_output=True,
        timeout=12,
        check=False,
    )
    if rendered.returncode or not rendered.stdout or len(rendered.stdout) > 32_000_000:
        raise ValueError("ocr_render_failed")
    recognized = subprocess.run(
        ["tesseract", "stdin", "stdout", "-l", "fas+ara+eng", "--psm", "6"],
        input=rendered.stdout,
        capture_output=True,
        timeout=12,
        check=False,
    )
    if recognized.returncode or len(recognized.stdout) > max_page_text_chars * 4:
        raise ValueError("ocr_failed")
    return recognized.stdout.decode("utf-8", errors="strict")


def _binary_version(binary: str, flag: str) -> str:
    completed = subprocess.run([binary, flag], capture_output=True, timeout=2, check=False)
    if completed.returncode != 0:
        raise ValueError("ocr_runtime_unavailable")
    output = (completed.stdout + completed.stderr).decode("utf-8", errors="replace").splitlines()
    if not output:
        raise ValueError("ocr_runtime_unavailable")
    # Read the installed binary's actual version, not an assumed package version.
    return output[0].strip()[:50]


def _pdf(data: bytes, max_pages: int, max_ocr_pages: int, max_page_text_chars: int) -> list[dict]:
    reader = PdfReader(BytesIO(data), strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= max_pages:
        raise ValueError("invalid_document")
    result = []
    ocr_count = 0
    parser_version = "pypdf/" + version("pypdf")
    ocr_versions = None
    for number, page in enumerate(reader.pages, 1):
        contents = page.get_contents()
        if contents is not None and len(contents.get_data()) > max_page_text_chars:
            raise ValueError("oversized_pdf_page")
        raw = page.extract_text() or ""
        has_digital_text = bool(raw.strip())
        # A text layer does not prove that raster content on the same page is
        # searchable. OCR image-bearing pages as well as image-only pages.
        needs_ocr = not has_digital_text or bool(page.images)
        if needs_ocr:
            ocr_count += 1
            if ocr_count > max_ocr_pages:
                raise ValueError("ocr_page_limit")
            if ocr_versions is None:
                ocr_versions = _binary_version("tesseract", "--version") + "; " + _binary_version("pdftoppm", "-v")
            recognized = _ocr_pdf_page(data, number, max_page_text_chars)
            if has_digital_text:
                # Preserve the independently extracted digital text. OCR sees
                # the rendered whole page and may repeat it; deduplication of
                # uncertain OCR output would risk discarding actual content.
                if recognized.strip():
                    raw = raw.rstrip() + "\n\n" + recognized.strip()
                    method = "hybrid_pdf_ocr"
                else:
                    method = "digital_pdf"
            else:
                raw = recognized
                method = "tesseract_ocr"
        else:
            method = "digital_pdf"
        if len(raw) > max_page_text_chars:
            raise ValueError("oversized_extraction")
        engine = parser_version if method == "digital_pdf" else (parser_version + "; " + ocr_versions)
        result.append({"number": number, "text": raw, "method": method, "engine_version": engine})
    return result


def extract(
    data: bytes, mime: str, max_bytes: int, max_pages: int, max_ocr_pages: int, max_page_text_chars: int
) -> list[dict]:
    if not data or len(data) > max_bytes:
        raise ValueError("invalid_document")
    if mime == "application/pdf":
        return _pdf(data, max_pages, max_ocr_pages, max_page_text_chars)
    if mime == _WORD_MIME:
        output = _docx(data)
        if len(output[0]["text"]) > max_page_text_chars:
            raise ValueError("oversized_extraction")
        return output
    if mime == "text/plain":
        text = data.decode("utf-8-sig")
        if len(text) > max_page_text_chars:
            raise ValueError("oversized_extraction")
        if any(ord(c) < 32 and c not in "\t\r\n" for c in text):
            raise ValueError("invalid_document")
        return [
            {
                "number": None,
                "text": text,
                "method": "utf8_text",
                "engine_version": f"utf8-sig/python/{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            }
        ]
    raise ValueError("unsupported_format")


def main() -> int:
    # Defensive upper bounds remain enforced in the subprocess even if invoked
    # without the validated parent provider or its configuration.
    if len(sys.argv) != 8:
        return 2
    try:
        max_bytes, max_pages, max_ocr_pages, memory_mb, cpu_seconds, max_page_text_chars = map(int, sys.argv[2:8])
    except ValueError:
        return 2
    if not (
        1024 <= max_bytes <= _MAX_BYTES
        and 1 <= max_pages <= _MAX_PAGES
        and 1 <= max_ocr_pages <= min(16, max_pages)
        and 128 <= memory_mb <= 1024
        and 2 <= cpu_seconds <= 60
        and 1024 <= max_page_text_chars <= _MAX_TEXT_PER_PAGE
    ):
        return 2
    _limits(memory_mb, cpu_seconds)
    try:
        data = sys.stdin.buffer.read(max_bytes + 1)
        result = extract(data, sys.argv[1], max_bytes, max_pages, max_ocr_pages, max_page_text_chars)
        if not any(item["text"].strip() for item in result):
            return 3
        encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode()
        if len(encoded) > 8_000_000:
            return 4
        sys.stdout.buffer.write(encoded)
        return 0
    except (Exception, subprocess.TimeoutExpired):
        # Only exit codes leave this subprocess; raw content and parser errors are not logged.
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
