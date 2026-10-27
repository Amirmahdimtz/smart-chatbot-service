"""Isolated, resource-bounded extractor process. Never invoke on unscanned input.

Called only by DocumentExtractor after the existing ClamAV gate. Its stdout is
protocol JSON, never application logging. Original file bytes remain immutable.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader

_MAX_BYTES = 5_242_880
_MAX_PAGES = 300
_MAX_OCR_PAGES = 8
_MAX_TEXT_PER_PAGE = 4_000_000
_WORD_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _limits() -> None:
    if os.name == "posix":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024, 768 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (32, 34))


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
            text = Paragraph(item, document._body).text.strip()
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
    return [{"number": None, "text": text, "method": "docx"}]


def _ocr_pdf_page(data: bytes, number: int) -> str:
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
    if recognized.returncode or len(recognized.stdout) > _MAX_TEXT_PER_PAGE:
        raise ValueError("ocr_failed")
    return recognized.stdout.decode("utf-8", errors="strict")


def _pdf(data: bytes) -> list[dict]:
    reader = PdfReader(BytesIO(data), strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= _MAX_PAGES:
        raise ValueError("invalid_document")
    result = []
    ocr_count = 0
    for number, page in enumerate(reader.pages, 1):
        contents = page.get_contents()
        if contents is not None and len(contents.get_data()) > 4_000_000:
            raise ValueError("oversized_pdf_page")
        raw = page.extract_text() or ""
        if not raw.strip():
            ocr_count += 1
            if ocr_count > _MAX_OCR_PAGES:
                raise ValueError("ocr_page_limit")
            raw = _ocr_pdf_page(data, number)
            method = "tesseract_ocr"
        else:
            method = "digital_pdf"
        if len(raw) > _MAX_TEXT_PER_PAGE:
            raise ValueError("oversized_extraction")
        result.append({"number": number, "text": raw, "method": method})
    return result


def extract(data: bytes, mime: str) -> list[dict]:
    if not data or len(data) > _MAX_BYTES:
        raise ValueError("invalid_document")
    if mime == "application/pdf":
        return _pdf(data)
    if mime == _WORD_MIME:
        return _docx(data)
    if mime == "text/plain":
        text = data.decode("utf-8-sig")
        if any(ord(c) < 32 and c not in "\t\r\n" for c in text):
            raise ValueError("invalid_document")
        return [{"number": None, "text": text, "method": "utf8_text"}]
    raise ValueError("unsupported_format")


def main() -> int:
    _limits()
    if len(sys.argv) != 2:
        return 2
    try:
        data = sys.stdin.buffer.read(_MAX_BYTES + 1)
        result = extract(data, sys.argv[1])
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
