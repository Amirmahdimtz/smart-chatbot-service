"""Loss-aware Persian normalization and deterministic structure-aware chunks.

Offsets always address the extractor's *original page text*, not an inferred PDF
byte offset or a guessed visual coordinate. No indexing/publication occurs here.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from uuid import UUID, uuid5

PROCESSOR_VERSION = "fa-structure-v1"
NORMALIZER_VERSION = "fa-nfc-normalizer-v1"
_TRANSLATION = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        **{chr(ord("۰") + i): str(i) for i in range(10)},
        **{chr(ord("٠") + i): str(i) for i in range(10)},
    }
)
_SPACES = re.compile(r"[\u00a0\u2000-\u200a\u202f\u205f\u3000]")
_BLANKS = re.compile(r"[ \t]+")
_PARAGRAPH = re.compile(r"\S[\s\S]*?(?=\n[ \t]*\n|\Z)")
_HEADING = re.compile(r"^(?:#{1,6}\s+|(?:فصل|بخش|باب|ماده)\s+\S+|(?:سوال|سؤال|پرسش)\s*[:：])")
_SENTENCE_END = re.compile(r"[.!؟?؛;]\s+")


class ProcessingRejected(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ExtractedPage:
    number: int | None
    text: str
    method: str  # digital_pdf, tesseract_ocr, docx or utf8_text
    engine_version: str = ""  # Real extractor emits parser + OCR binary versions


@dataclass(frozen=True)
class ProcessedChunk:
    id: UUID
    ordinal: int
    page: int | None
    start: int
    end: int
    original: str
    canonical: str
    section: str | None
    method: str
    checksum: str
    processor_version: str = PROCESSOR_VERSION
    normalizer_version: str = NORMALIZER_VERSION
    engine_version: str = ""


def normalize_persian(text: str) -> str:
    """NFC only (not NFKC); original extraction remains available for quotations."""
    normalized = unicodedata.normalize("NFC", text).translate(_TRANSLATION)
    normalized = _SPACES.sub(" ", normalized)
    normalized = _BLANKS.sub(" ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    return normalized.strip()


def _split_span(text: str, start: int, end: int, max_chars: int):
    """Find sentence/space boundaries; hard-split only if no safe boundary exists."""
    while end - start > max_chars:
        upper = start + max_chars
        portion = text[start:upper]
        breaks = [m.end() for m in _SENTENCE_END.finditer(portion)]
        cut = start + breaks[-1] if breaks else -1
        if cut <= start + max_chars // 3:
            cut = start + max(portion.rfind(" "), portion.rfind("\n")) + 1
        if cut <= start + max_chars // 3:
            cut = upper
        yield start, cut
        start = cut
        while start < end and text[start].isspace():
            start += 1
    if start < end:
        yield start, end


def chunk_pages(
    version_id: UUID,
    pages: list[ExtractedPage],
    *,
    max_chars: int = 1200,
    overlap: int = 0,
) -> list[ProcessedChunk]:
    if not 256 <= max_chars <= 4000 or not 0 <= overlap <= min(256, max_chars // 4):
        raise ValueError("Invalid chunk boundaries")
    if not pages or len(pages) > 300:
        raise ProcessingRejected("invalid_pages")
    chunks: list[ProcessedChunk] = []
    section: str | None = None

    def append(page: ExtractedPage, start: int, end: int) -> None:
        raw = page.text[start:end]
        canonical = normalize_persian(raw)
        if not canonical:
            return
        ordinal = len(chunks)
        checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        stable = uuid5(
            version_id,
            f"{PROCESSOR_VERSION}:{page.number}:{start}:{end}:{checksum}",
        )
        chunks.append(
            ProcessedChunk(
                id=stable,
                ordinal=ordinal,
                page=page.number,
                start=start,
                end=end,
                original=raw,
                canonical=canonical,
                section=section,
                method=page.method,
                checksum=checksum,
                processor_version=PROCESSOR_VERSION,
                normalizer_version=NORMALIZER_VERSION,
                engine_version=page.engine_version,
            )
        )

    for page in pages:
        if page.number is not None and page.number < 1:
            raise ProcessingRejected("invalid_page_number")
        if not isinstance(page.text, str) or len(page.text) > 4_000_000:
            raise ProcessingRejected("invalid_extraction")
        spans = list(_PARAGRAPH.finditer(page.text))
        group_start: int | None = None
        group_end = 0
        for match in spans:
            block_start, block_end = match.span()
            if not normalize_persian(match.group()):
                continue
            heading = bool(_HEADING.match(match.group().lstrip()))
            if heading:
                if group_start is not None:
                    append(page, group_start, group_end)
                    group_start = None
                section = normalize_persian(match.group().split("\n", 1)[0])[:200]
            if block_end - block_start > max_chars:
                if group_start is not None:
                    append(page, group_start, group_end)
                    group_start = None
                for start, end in _split_span(page.text, block_start, block_end, max_chars):
                    append(page, start, end)
                group_end = block_end
                continue
            if group_start is not None and block_end - group_start > max_chars:
                append(page, group_start, group_end)
                group_start = None
            if group_start is None:
                # A backward slice only includes actual page text, never fabricated context.
                group_start = max(0, block_start - overlap) if chunks and overlap else block_start
            group_end = block_end
        if group_start is not None:
            append(page, group_start, group_end)

    if not chunks:
        raise ProcessingRejected("no_extractable_text")
    return chunks
