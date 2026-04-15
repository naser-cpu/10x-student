"""Course tool handlers."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..canvas.client import CanvasClient


async def handle_list_courses(canvas_client: CanvasClient) -> list[dict[str, Any]]:
    return [asdict(course) for course in await canvas_client.list_courses()]
