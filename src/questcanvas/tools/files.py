"""File tool handlers."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..services.files import FileService


async def handle_list_course_files(
    file_service: FileService,
    course_id: int,
    module_id: int | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    return [
        asdict(file_view)
        for file_view in await file_service.list_course_files(
            course_id,
            module_id=module_id,
            search=search,
        )
    ]


async def handle_get_file_text(
    file_service: FileService,
    file_id: int,
    max_units: int = 40,
) -> dict[str, Any]:
    extraction = await file_service.get_file_text(file_id, max_units=max_units)
    return asdict(extraction)
