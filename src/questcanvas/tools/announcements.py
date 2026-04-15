"""Announcement tool handlers."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..canvas.client import CanvasClient


async def handle_list_announcements(
    canvas_client: CanvasClient,
    course_id: int | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    return [
        asdict(item) for item in await canvas_client.list_announcements(course_id=course_id, limit=limit)
    ]
