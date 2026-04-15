"""Common extractor models and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..canvas.types import CanvasFile


@dataclass(slots=True)
class ExtractionUnit:
    unit_type: str
    unit_number: int
    text: str


@dataclass(slots=True)
class ExtractionResult:
    file_id: int
    file_name: str
    content_type: str
    unit_type: str
    units_extracted: int
    truncated: bool
    text: str
    units: list[ExtractionUnit]


class Extractor(Protocol):
    def supports(self, canvas_file: CanvasFile) -> bool:
        """Return whether this extractor can handle the file."""

    def extract(
        self,
        canvas_file: CanvasFile,
        content: bytes,
        *,
        max_units: int,
    ) -> ExtractionResult:
        """Extract readable text from file content."""


def build_result(
    canvas_file: CanvasFile,
    *,
    unit_type: str,
    units: list[ExtractionUnit],
    max_units: int,
) -> ExtractionResult:
    limited_units = units[:max_units]
    truncated = len(units) > max_units
    combined_text = "\n\n".join(unit.text for unit in limited_units)

    return ExtractionResult(
        file_id=canvas_file.id,
        file_name=canvas_file.effective_name,
        content_type=canvas_file.content_type or "application/octet-stream",
        unit_type=unit_type,
        units_extracted=len(limited_units),
        truncated=truncated,
        text=combined_text,
        units=limited_units,
    )
