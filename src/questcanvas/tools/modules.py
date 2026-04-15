"""Module tool handlers."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..canvas.client import CanvasClient


async def handle_list_modules(
    canvas_client: CanvasClient,
    course_id: int,
) -> list[dict[str, Any]]:
    modules = await canvas_client.list_modules(course_id)
    for module in modules:
        module.items = await canvas_client.list_module_items(course_id, module.id)
    return [asdict(module) for module in modules]
