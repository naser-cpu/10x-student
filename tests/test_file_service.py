from __future__ import annotations

import unittest

from questcanvas.canvas.types import CanvasFile, CanvasModuleItem
from questcanvas.services.files import FileService


class StubCanvasClient:
    def __init__(self) -> None:
        self.file = CanvasFile(
            id=10,
            course_id=1,
            display_name="lecture.txt",
            filename="lecture.txt",
            content_type="text/plain",
            url="https://download",
            size=12,
            updated_at="2026-04-13T00:00:00Z",
        )

    async def list_course_files(self, course_id: int, search: str | None = None) -> list[CanvasFile]:
        return [self.file, CanvasFile(
            id=11,
            course_id=course_id,
            display_name="archive.zip",
            filename="archive.zip",
            content_type="application/zip",
            url="https://download-zip",
            size=14,
            updated_at=None,
        )]

    async def list_module_items(self, course_id: int, module_id: int) -> list[CanvasModuleItem]:
        return [
            CanvasModuleItem(
                id=1,
                module_id=module_id,
                title="Lecture",
                type="File",
                content_id=10,
                html_url=None,
                url=None,
            )
        ]

    async def get_file(self, file_id: int) -> CanvasFile:
        return self.file

    async def download_file(self, canvas_file: CanvasFile) -> bytes:
        return b"First section\n\nSecond section\n\nThird section"


class FileServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_course_files_marks_extractable(self) -> None:
        service = FileService(StubCanvasClient())

        files = await service.list_course_files(1)

        self.assertEqual(len(files), 2)
        self.assertTrue(files[0].extractable)
        self.assertFalse(files[1].extractable)

    async def test_list_course_files_filters_by_module(self) -> None:
        service = FileService(StubCanvasClient())

        files = await service.list_course_files(1, module_id=99)

        self.assertEqual([item.file_id for item in files], [10])

    async def test_get_file_text_applies_truncation(self) -> None:
        service = FileService(StubCanvasClient())

        result = await service.get_file_text(10, max_units=2)

        self.assertEqual(result.units_extracted, 2)
        self.assertTrue(result.truncated)
        self.assertIn("[Section 1]", result.text)
