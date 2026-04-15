"""Assignment tool handlers."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..canvas.client import CanvasClient


async def handle_list_assignments(
    canvas_client: CanvasClient,
    course_id: int,
) -> list[dict[str, Any]]:
    return [asdict(item) for item in await canvas_client.list_assignments(course_id)]
