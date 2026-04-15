"""PDF extraction via PyMuPDF."""

from __future__ import annotations

from ..canvas.types import CanvasFile
from ..errors import ExtractionError, MissingDependencyError
from .base import ExtractionUnit, ExtractionResult, build_result


class PdfExtractor:
    """Extractor for PDF files with page markers."""

    def supports(self, canvas_file: CanvasFile) -> bool:
        content_type = (canvas_file.content_type or "").lower()
        return content_type == "application/pdf" or canvas_file.effective_name.lower().endswith(".pdf")

    def extract(
        self,
        canvas_file: CanvasFile,
        content: bytes,
        *,
        max_units: int,
    ) -> ExtractionResult:
        try:
            import fitz
        except ImportError as exc:
            raise MissingDependencyError(
                "PyMuPDF is required for PDF extraction. Install questcanvas dependencies first."
            ) from exc

        try:
            document = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise ExtractionError(f"Could not open PDF file {canvas_file.effective_name}.") from exc

        units: list[ExtractionUnit] = []
        for page_number, page in enumerate(document, start=1):
            page_text = page.get_text("text").strip()
            if not page_text:
                continue
            units.append(
                ExtractionUnit(
                    unit_type="page",
                    unit_number=page_number,
                    text=f"[Page {page_number}]\n{page_text}",
                )
            )

        return build_result(canvas_file, unit_type="page", units=units, max_units=max_units)
