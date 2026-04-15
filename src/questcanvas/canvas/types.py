"""Typed Canvas API payload models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _integer(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class Course:
    id: int
    name: str
    course_code: str | None = None
    workflow_state: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Course":
        return cls(
            id=int(payload["id"]),
            name=_string(payload.get("name")) or f"Course {payload['id']}",
            course_code=_string(payload.get("course_code")),
            workflow_state=_string(payload.get("workflow_state")),
        )


@dataclass(slots=True)
class CanvasFile:
    id: int
    course_id: int | None
    display_name: str
    filename: str | None
    content_type: str | None
    url: str | None
    size: int | None
    updated_at: str | None

    @property
    def effective_name(self) -> str:
        return self.display_name or self.filename or f"file-{self.id}"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CanvasFile":
        return cls(
            id=int(payload["id"]),
            course_id=_integer(payload.get("course_id")),
            display_name=_string(payload.get("display_name"))
            or _string(payload.get("filename"))
            or f"file-{payload['id']}",
            filename=_string(payload.get("filename")),
            content_type=_string(payload.get("content-type"))
            or _string(payload.get("content_type")),
            url=_string(payload.get("url")),
            size=_integer(payload.get("size")),
            updated_at=_string(payload.get("updated_at")),
        )


@dataclass(slots=True)
class CanvasModuleItem:
    id: int
    module_id: int
    title: str
    type: str | None
    content_id: int | None
    html_url: str | None
    url: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], module_id: int) -> "CanvasModuleItem":
        return cls(
            id=int(payload["id"]),
            module_id=module_id,
            title=_string(payload.get("title")) or f"Item {payload['id']}",
            type=_string(payload.get("type")),
            content_id=_integer(payload.get("content_id")),
            html_url=_string(payload.get("html_url")),
            url=_string(payload.get("url")),
        )


@dataclass(slots=True)
class CanvasModule:
    id: int
    name: str
    position: int | None
    items_count: int | None
    items: list[CanvasModuleItem] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CanvasModule":
        return cls(
            id=int(payload["id"]),
            name=_string(payload.get("name")) or f"Module {payload['id']}",
            position=_integer(payload.get("position")),
            items_count=_integer(payload.get("items_count")),
        )


@dataclass(slots=True)
class CanvasAssignment:
    id: int
    name: str
    due_at: str | None
    html_url: str | None
    description: str | None
    points_possible: float | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CanvasAssignment":
        return cls(
            id=int(payload["id"]),
            name=_string(payload.get("name")) or f"Assignment {payload['id']}",
            due_at=_string(payload.get("due_at")),
            html_url=_string(payload.get("html_url")),
            description=_string(payload.get("description")),
            points_possible=_float(payload.get("points_possible")),
        )


@dataclass(slots=True)
class CanvasAnnouncement:
    id: int
    title: str
    message: str | None
    posted_at: str | None
    html_url: str | None
    course_id: int | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CanvasAnnouncement":
        return cls(
            id=int(payload["id"]),
            title=_string(payload.get("title")) or f"Announcement {payload['id']}",
            message=_string(payload.get("message")),
            posted_at=_string(payload.get("posted_at")) or _string(payload.get("created_at")),
            html_url=_string(payload.get("html_url")),
            course_id=_integer(payload.get("context_code", "").split("_")[-1])
            if _string(payload.get("context_code"))
            else _integer(payload.get("course_id")),
        )
