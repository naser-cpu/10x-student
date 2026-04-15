"""DOCX extraction via python-docx."""

from __future__ import annotations

from io import BytesIO

from ..canvas.types import CanvasFile
from ..errors import ExtractionError, MissingDependencyError
from .base import ExtractionUnit, ExtractionResult, build_result


class DocxExtractor:
    """Extractor for DOCX files with paragraph markers."""

    def supports(self, canvas_file: CanvasFile) -> bool:
        content_type = (canvas_file.content_type or "").lower()
        return (
            content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            or canvas_file.effective_name.lower().endswith(".docx")
        )

    def extract(
        self,
        canvas_file: CanvasFile,
        content: bytes,
        *,
        max_units: int,
    ) -> ExtractionResult:
        try:
            from docx import Document
        except ImportError as exc:
            raise MissingDependencyError(
                "python-docx is required for DOCX extraction. Install questcanvas dependencies first."
            ) from exc

        try:
            document = Document(BytesIO(content))
        except Exception as exc:
            raise ExtractionError(f"Could not open DOCX file {canvas_file.effective_name}.") from exc

        units: list[ExtractionUnit] = []
        for paragraph_number, paragraph in enumerate(document.paragraphs, start=1):
            text = paragraph.text.strip()
            if not text:
                continue
            units.append(
                ExtractionUnit(
                    unit_type="paragraph",
                    unit_number=paragraph_number,
                    text=f"[Paragraph {paragraph_number}]\n{text}",
                )
            )

        return build_result(canvas_file, unit_type="paragraph", units=units, max_units=max_units)
