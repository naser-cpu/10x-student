"""Course file listing and extraction service."""

from __future__ import annotations

from dataclasses import dataclass

from ..canvas.client import CanvasClient
from ..canvas.types import CanvasFile, CanvasModuleItem
from ..extractors import ExtractorRegistry, ExtractionResult


@dataclass(slots=True)
class CourseFileView:
    file_id: int
    course_id: int | None
    file_name: str
    content_type: str | None
    size: int | None
    updated_at: str | None
    extractable: bool
    module_id: int | None = None


class FileService:
    """Lists study-material files and extracts readable text."""

    def __init__(
        self,
        canvas_client: CanvasClient,
        *,
        extractor_registry: ExtractorRegistry | None = None,
    ) -> None:
        self.canvas_client = canvas_client
        self.extractor_registry = extractor_registry or ExtractorRegistry()

    async def list_course_files(
        self,
        course_id: int,
        module_id: int | None = None,
        search: str | None = None,
    ) -> list[CourseFileView]:
        files = await self.canvas_client.list_course_files(course_id, search=search)
        allowed_file_ids: set[int] | None = None
        if module_id is not None:
            items = await self.canvas_client.list_module_items(course_id, module_id)
            allowed_file_ids = {
                item.content_id
                for item in items
                if _module_item_points_to_file(item) and item.content_id is not None
            }

        file_views: list[CourseFileView] = []
        for canvas_file in files:
            if allowed_file_ids is not None and canvas_file.id not in allowed_file_ids:
                continue
            file_views.append(self._to_view(canvas_file, module_id=module_id))
        return file_views

    def _to_view(self, canvas_file: CanvasFile, *, module_id: int | None) -> CourseFileView:
        try:
            self.extractor_registry.for_file(canvas_file)
            extractable = True
        except Exception:
            extractable = False

        return CourseFileView(
            file_id=canvas_file.id,
            course_id=canvas_file.course_id,
            file_name=canvas_file.effective_name,
            content_type=canvas_file.content_type,
            size=canvas_file.size,
            updated_at=canvas_file.updated_at,
            extractable=extractable,
            module_id=module_id,
        )

    async def get_file_text(self, file_id: int, max_units: int = 40) -> ExtractionResult:
        if max_units <= 0:
            raise ValueError("max_units must be at least 1.")

        canvas_file = await self.canvas_client.get_file(file_id)
        extractor = self.extractor_registry.for_file(canvas_file)
        content = await self.canvas_client.download_file(canvas_file)
        return extractor.extract(canvas_file, content, max_units=max_units)


def _module_item_points_to_file(item: CanvasModuleItem) -> bool:
    item_type = (item.type or "").lower()
    return item_type == "file"
