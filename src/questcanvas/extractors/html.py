"""HTML extraction helpers."""

from __future__ import annotations

from html.parser import HTMLParser

from ..canvas.types import CanvasFile
from .base import ExtractionResult
from .text import TextExtractor, decode_text_content

HTML_EXTENSIONS = {".html", ".htm"}


class _ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


class HtmlExtractor:
    """Extractor that converts HTML content into readable text sections."""

    def __init__(self) -> None:
        self._text_extractor = TextExtractor()

    def supports(self, canvas_file: CanvasFile) -> bool:
        content_type = (canvas_file.content_type or "").lower()
        if content_type.startswith("text/html"):
            return True
        lower_name = canvas_file.effective_name.lower()
        return any(lower_name.endswith(extension) for extension in HTML_EXTENSIONS)

    def extract(
        self,
        canvas_file: CanvasFile,
        content: bytes,
        *,
        max_units: int,
    ) -> ExtractionResult:
        parser = _ReadableHTMLParser()
        parser.feed(decode_text_content(content))
        text = "\n\n".join(parser.parts)
        return self._text_extractor.extract(canvas_file, text.encode("utf-8"), max_units=max_units)
