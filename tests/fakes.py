"""Test doubles for async HTTP and service dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FakeResponse:
    status_code: int = 200
    json_data: Any = None
    text: str = ""
    content: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)

    def json(self) -> Any:
        return self.json_data


class FakeAsyncHttpClient:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> FakeResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers or {},
                "params": params or {},
            }
        )
        if not self.responses:
            raise AssertionError("No fake responses left.")
        return self.responses.pop(0)

    async def aclose(self) -> None:
        return None
