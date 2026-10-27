"""Phase06 page-specific source spans and durable storage chunk-cap regression."""

from uuid import uuid4

import pytest

from src.core.services.persian_text.persian_processing import (
    ExtractedPage,
    ProcessingRejected,
    chunk_pages,
    normalize_persian,
)


def test_offsets_are_page_relative_and_deterministic():
    pages = [
        ExtractedPage(1, "ماده ۱\n" + "الف" * 290, "digital_pdf"),
        ExtractedPage(2, "فصل دوم\n" + "ب" * 305, "digital_pdf"),
        ExtractedPage(3, "سؤال: پاسخ آخر؟\nپاسخ: " + "پ" * 280, "digital_pdf"),
    ]
    version = uuid4()
    first = chunk_pages(version, pages, max_chars=256)
    assert first == chunk_pages(version, pages, max_chars=256)
    assert {part.page for part in first} == {1, 2, 3}
    for page in pages:
        spans = [part for part in first if part.page == page.number]
        assert spans
        assert all(0 <= part.start < part.end <= len(page.text) for part in spans)
        assert all(page.text[part.start : part.end] == part.original for part in spans)
        assert all(part.canonical == normalize_persian(part.original) for part in spans)
        assert page.text[-15:] in "".join(part.original for part in spans)


def test_chunk_cap_exact_boundary_and_one_over():
    version = uuid4()
    data = "الف" * (4096 * 256)
    accepted = chunk_pages(version, [ExtractedPage(None, data, "utf8_text")], max_chars=256)
    assert len(accepted) == 4096
    assert all(part.ordinal == i for i, part in enumerate(accepted))
    with pytest.raises(ProcessingRejected, match="too_many_chunks"):
        chunk_pages(version, [ExtractedPage(None, data + "الف", "utf8_text")], max_chars=256)
