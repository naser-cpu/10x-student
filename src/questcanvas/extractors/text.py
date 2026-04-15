"""Plain-text extraction helpers."""

from __future__ import annotations

import re

from ..canvas.types import CanvasFile
from .base import ExtractionUnit, ExtractionResult, build_result

TEXT_MIME_PREFIXES = ("text/",)
TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv"}


def split_text_sections(text: str) -> list[str]:
    """Split text into readable units while preserving order."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    sections = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    if sections:
        return sections
    return [line.strip() for line in normalized.splitlines() if line.strip()]


def decode_text_content(content: bytes) -> str:
    """Decode text-like content safely."""

    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


class TextExtractor:
    """Extractor for TXT, Markdown, CSV, and similar text files."""

    def supports(self, canvas_file: CanvasFile) -> bool:
        content_type = (canvas_file.content_type or "").lower()
        if any(content_type.startswith(prefix) for prefix in TEXT_MIME_PREFIXES):
            return True
        lower_name = canvas_file.effective_name.lower()
        return any(lower_name.endswith(extension) for extension in TEXT_EXTENSIONS)

    def extract(
        self,
        canvas_file: CanvasFile,
        content: bytes,
        *,
        max_units: int,
    ) -> ExtractionResult:
        text = decode_text_content(content)
        sections = split_text_sections(text)
        units = [
            ExtractionUnit(
                unit_type="section",
                unit_number=index,
                text=f"[Section {index}]\n{section}",
            )
            for index, section in enumerate(sections, start=1)
        ]
        return build_result(canvas_file, unit_type="section", units=units, max_units=max_units)
