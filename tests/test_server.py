from __future__ import annotations

import unittest

from questcanvas.config import AppConfig
from questcanvas.server import QuestCanvasApp
from questcanvas.services.files import FileService


class StubAppCanvasClient:
    async def aclose(self) -> None:
        return None

    async def list_courses(self):
        from questcanvas.canvas.types import Course

        return [Course(id=1, name="Databases")]

    async def list_modules(self, course_id: int):
        from questcanvas.canvas.types import CanvasModule

        return [CanvasModule(id=1, name="Week 1", position=1, items_count=0)]

    async def list_module_items(self, course_id: int, module_id: int):
        return []

    async def list_assignments(self, course_id: int):
        from questcanvas.canvas.types import CanvasAssignment

        return [CanvasAssignment(id=2, name="HW 1", due_at=None, html_url=None, description=None, points_possible=None)]

    async def list_announcements(self, course_id: int | None = None, limit: int = 5):
        from questcanvas.canvas.types import CanvasAnnouncement

        return [CanvasAnnouncement(id=3, title="Welcome", message=None, posted_at=None, html_url=None, course_id=course_id)]


class StubFileService:
    async def list_course_files(self, course_id: int, module_id: int | None = None, search: str | None = None):
        return []

    async def get_file_text(self, file_id: int, max_units: int = 40):
        return {
            "file_id": file_id,
            "file_name": "lecture.txt",
            "content_type": "text/plain",
            "unit_type": "section",
            "units_extracted": 1,
            "truncated": False,
            "text": "hello",
            "units": [],
        }


class ServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_app_methods_delegate(self) -> None:
        app = QuestCanvasApp(
            config=AppConfig(
                canvas_base_url="https://canvas.example.edu",
                canvas_token="secret",
                data_dir=__import__("pathlib").Path("/tmp/questcanvas"),
            ),
            token_provider=__import__("questcanvas.auth", fromlist=["StaticTokenProvider"]).StaticTokenProvider("secret"),
            canvas_client=StubAppCanvasClient(),
            file_service=StubFileService(),
        )

        self.assertEqual((await app.list_courses())[0]["name"], "Databases")
        self.assertEqual((await app.get_assignments(1))[0]["name"], "HW 1")
        self.assertEqual((await app.get_announcements(1))[0]["title"], "Welcome")
