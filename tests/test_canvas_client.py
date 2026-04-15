from __future__ import annotations

import unittest

from questcanvas.auth import StaticTokenProvider
from questcanvas.canvas.client import CanvasClient
from questcanvas.errors import CanvasRateLimitError

from tests.fakes import FakeAsyncHttpClient, FakeResponse


class CanvasClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_courses_auto_paginates(self) -> None:
        fake_http = FakeAsyncHttpClient(
            [
                FakeResponse(
                    json_data=[{"id": 1, "name": "Networks", "workflow_state": "available"}],
                    headers={
                        "Link": '<https://canvas.example.edu/api/v1/courses?page=2>; rel="next"'
                    },
                ),
                FakeResponse(
                    json_data=[{"id": 2, "name": "Operating Systems", "workflow_state": "available"}],
                ),
            ]
        )
        client = CanvasClient(
            "https://canvas.example.edu",
            StaticTokenProvider("secret-token"),
            http_client=fake_http,
        )

        with self.assertLogs("questcanvas.canvas.client", level="INFO") as captured:
            courses = await client.list_courses()

        self.assertEqual([course.id for course in courses], [1, 2])
        self.assertEqual(fake_http.calls[0]["params"]["per_page"], 100)
        self.assertEqual(fake_http.calls[1]["params"], {})
        self.assertNotIn("secret-token", "\n".join(captured.output))

    async def test_rate_limit_retries_then_succeeds(self) -> None:
        slept: list[float] = []

        async def fake_sleep(delay: float) -> None:
            slept.append(delay)

        fake_http = FakeAsyncHttpClient(
            [
                FakeResponse(status_code=429, text="too many requests"),
                FakeResponse(json_data={"id": 42, "display_name": "lecture.txt", "url": "https://files"}),
            ]
        )
        client = CanvasClient(
            "https://canvas.example.edu",
            StaticTokenProvider("secret-token"),
            http_client=fake_http,
            sleep_func=fake_sleep,
            max_retries=1,
        )

        file_details = await client.get_file(42)

        self.assertEqual(file_details.id, 42)
        self.assertEqual(len(slept), 1)

    async def test_rate_limit_exhaustion_raises(self) -> None:
        async def fake_sleep(_: float) -> None:
            return None

        fake_http = FakeAsyncHttpClient([FakeResponse(status_code=429, text="too many requests")])
        client = CanvasClient(
            "https://canvas.example.edu",
            StaticTokenProvider("secret-token"),
            http_client=fake_http,
            sleep_func=fake_sleep,
            max_retries=0,
        )

        with self.assertRaises(CanvasRateLimitError):
            await client.list_courses()
