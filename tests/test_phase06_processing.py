"""Synthetic Phase06 A tests + real isolated PDF/DOCX/Persian OCR B fixtures."""

from __future__ import annotations

import asyncio
import hashlib
import io
import shutil
from uuid import uuid4

import pytest
from docx import Document
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from src.core.services.ingestion.upload_validation import UploadRejected, validate_content
from src.core.services.persian_text.persian_processing import (
    ExtractedPage,
    ProcessingRejected,
    chunk_pages,
    normalize_persian,
)
from src.infrastructure.providers.document.document_extractor import DocumentExtractor

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_loss_aware_persian_arabic_mixed_normalization():
    raw = "علي كاظمي\u00a0در ماده ١٢ و سال ۱۴۰۵ گفت: آیه \u200c۱۲"
    expected = "علی کاظمی در ماده 12 و سال 1405 گفت: آیه \u200c12"
    assert normalize_persian(raw) == expected
    assert "علي" in raw and "علي" not in normalize_persian(raw)
    assert normalize_persian("Hello GPT-6 | سلام ٣") == "Hello GPT-6 | سلام 3"


def test_stable_chunk_ids_and_true_raw_spans():
    version_id = uuid4()
    raw = "ماده ۱۲\nشرح قرارداد و آثار آن.\n\nسؤال: مسئول کیست؟\nپاسخ: مدیر واحد."
    pages = [ExtractedPage(2, raw, "digital_pdf")]
    first = chunk_pages(version_id, pages, max_chars=256)
    second = chunk_pages(version_id, pages, max_chars=256)
    assert first == second
    assert first[0].page == 2
    assert all(raw[item.start : item.end] == item.original for item in first)
    assert all(item.checksum == hashlib.sha256(item.canonical.encode()).hexdigest() for item in first)
    assert all(item.id.version == 5 for item in first)
    assert first[0].section is not None
    assert first[0].canonical.startswith("ماده 12")
    assert chunk_pages(uuid4(), pages, max_chars=256)[0].id != first[0].id


def test_no_fabricated_citation_or_empty_chunk():
    with pytest.raises(ProcessingRejected, match="no_extractable_text"):
        chunk_pages(uuid4(), [ExtractedPage(None, "   \n\n", "utf8_text")])
    with pytest.raises(ProcessingRejected, match="invalid_page_number"):
        chunk_pages(uuid4(), [ExtractedPage(0, "Hello", "digital_pdf")])
    with pytest.raises(ValueError, match="Invalid chunk"):
        chunk_pages(uuid4(), [ExtractedPage(None, "Hello", "utf8_text")], max_chars=200)


def test_long_document_is_bounded_and_deterministic():
    raw = "ماده ۱.\n" + ("این بند شامل عبارت فارسی و استناد صحیح است. " * 90)
    result = chunk_pages(uuid4(), [ExtractedPage(None, raw, "utf8_text")], max_chars=256)
    assert len(result) >= 4
    assert all(0 < item.end - item.start <= 256 for item in result)
    assert all(raw[item.start : item.end] == item.original for item in result)


def _digital_pdf() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    contents = DecodedStreamObject()
    contents.set_data(b"BT /F1 20 Tf 72 720 Td (Hello digital PDF evidence) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(contents)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_real_digital_pdf_extraction_page_and_span():
    data = _digital_pdf()
    validate_content(data, "application/pdf")
    pages = asyncio.run(DocumentExtractor().extract_async(data, "application/pdf"))
    assert len(pages) == 1
    assert pages[0].number == 1
    assert pages[0].method == "digital_pdf"
    assert "digital PDF evidence" in pages[0].text
    pieces = chunk_pages(uuid4(), pages)
    assert pieces[0].original == pages[0].text[pieces[0].start : pieces[0].end]


def test_real_docx_paragraphs_and_table_extraction():
    document = Document()
    document.add_heading("بخش اول", level=1)
    document.add_paragraph("متن فارسی و Arabic")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "عنوان", "پاسخ"
    table.cell(1, 0).text, table.cell(1, 1).text = "سؤال", "گزینه"
    output = io.BytesIO()
    document.save(output)
    data = output.getvalue()
    validate_content(data, DOCX_MIME)
    pages = asyncio.run(DocumentExtractor().extract_async(data, DOCX_MIME))
    assert len(pages) == 1
    assert pages[0].number is None  # Word has no defensible fixed PDF page coordinates.
    assert "عنوان | پاسخ" in pages[0].text
    assert "سؤال | گزینه" in pages[0].text
    assert all(item.page is None for item in chunk_pages(uuid4(), pages))


def test_malformed_word_and_pdf_fail_closed():
    with pytest.raises(UploadRejected):
        validate_content(b"PK\x03\x04broken", DOCX_MIME)
    with pytest.raises(UploadRejected):
        validate_content(b"%PDF-missing-trailer", "application/pdf")
    with pytest.raises(ProcessingRejected):
        asyncio.run(DocumentExtractor().extract_async(b"not a PDF", "application/pdf"))


@pytest.mark.skipif(
    not shutil.which("pdftoppm") or not shutil.which("tesseract"),
    reason="Real Poppler and Tesseract OCR binaries not provisioned",
)
def _character_error_rate(actual: str, expected: str) -> float:
    """Levenshtein distance divided by ground-truth codepoint count."""
    previous = list(range(len(expected) + 1))
    for i, character in enumerate(actual, 1):
        row = [i]
        for j, reference in enumerate(expected, 1):
            row.append(
                min(
                    previous[j] + 1,
                    row[j - 1] + 1,
                    previous[j - 1] + (character != reference),
                )
            )
        previous = row
    return previous[-1] / len(expected)


def test_real_scanned_persian_pdf_ocr():
    # PIL raster-only PDF: no hidden text layer and no simulated OCR response.
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 75)
    image = Image.new("RGB", (1300, 240), "white")
    ImageDraw.Draw(image).text((1240, 48), "سلام دنیا", font=font, fill="black", anchor="ra", direction="rtl")
    pdf = io.BytesIO()
    image.save(pdf, format="PDF", resolution=180)
    data = pdf.getvalue()
    validate_content(data, "application/pdf")
    pages = asyncio.run(DocumentExtractor().extract_async(data, "application/pdf"))
    assert pages[0].method == "tesseract_ocr"
    assert pages[0].number == 1
    expected = "سلام دنیا"
    observed = normalize_persian(pages[0].text)
    cer = _character_error_rate(observed, expected)
    print(f"Phase06 scanned-PDF Persian OCR synthetic CER={cer:.3f}")
    assert cer <= 0.20, (observed, expected, cer)
    assert chunk_pages(uuid4(), pages)[0].method == "tesseract_ocr"
