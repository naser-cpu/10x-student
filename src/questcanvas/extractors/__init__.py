"""File extraction registry."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..canvas.types import CanvasFile
from ..errors import UnsupportedFileTypeError
from .base import Extractor, ExtractionResult, ExtractionUnit
from .docx import DocxExtractor
from .html import HtmlExtractor
from .pdf import PdfExtractor
from .pptx import PptxExtractor
from .text import TextExtractor


@dataclass(slots=True)
class ExtractorRegistry:
    """Selects the right extractor for a given Canvas file."""

    extractors: list[Extractor] = field(
        default_factory=lambda: [
            PdfExtractor(),
            PptxExtractor(),
            DocxExtractor(),
            HtmlExtractor(),
            TextExtractor(),
        ]
    )

    def for_file(self, canvas_file: CanvasFile) -> Extractor:
        for extractor in self.extractors:
            if extractor.supports(canvas_file):
                return extractor
        raise UnsupportedFileTypeError(
            f"File type for {canvas_file.effective_name} is not supported for extraction yet."
        )


__all__ = [
    "ExtractionResult",
    "ExtractionUnit",
    "ExtractorRegistry",
]
