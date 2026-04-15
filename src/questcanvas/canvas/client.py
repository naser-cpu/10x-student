"""Async Canvas API client."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Protocol
from urllib.parse import urljoin, urlparse

from ..auth import TokenProvider
from ..errors import CanvasRateLimitError, CanvasResponseError
from .pagination import get_next_link
from .rate_limits import get_budget_delay, get_retry_delay, is_throttle_response
from .types import (
    CanvasAnnouncement,
    CanvasAssignment,
    CanvasFile,
    CanvasModule,
    CanvasModuleItem,
    Course,
)

LOGGER = logging.getLogger(__name__)


class HttpResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]
    text: str
    content: bytes

    def json(self) -> Any:
        """Return decoded JSON content."""


class AsyncHttpClient(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> HttpResponse:
        """Issue an asynchronous HTTP request."""

    async def aclose(self) -> None:
        """Close the client if needed."""


class CanvasClient:
    """Typed async wrapper around the Canvas REST APIs used in V1."""

    def __init__(
        self,
        base_url: str,
        token_provider: TokenProvider,
        *,
        http_client: AsyncHttpClient | None = None,
        sleep_func: Callable[[float], Awaitable[None]] = asyncio.sleep,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token_provider = token_provider
        self._http_client = http_client
        self._owns_http_client = http_client is None
        self._sleep = sleep_func
        self._max_retries = max_retries

    async def aclose(self) -> None:
        if self._owns_http_client and self._http_client is not None:
            await self._http_client.aclose()

    async def _get_http_client(self) -> AsyncHttpClient:
        if self._http_client is None:
            import httpx

            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    def _make_url(self, path_or_url: str) -> str:
        parsed = urlparse(path_or_url)
        if parsed.scheme and parsed.netloc:
            return path_or_url
        return urljoin(f"{self.base_url}/", path_or_url.lstrip("/"))

    @staticmethod
    def _safe_path(path_or_url: str) -> str:
        parsed = urlparse(path_or_url)
        return parsed.path or path_or_url

    async def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> HttpResponse:
        client = await self._get_http_client()
        token = await self.token_provider.get_token()
        url = self._make_url(path_or_url)

        for attempt in range(self._max_retries + 1):
            started = time.perf_counter()
            response = await client.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, */*",
                },
                params=params,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            LOGGER.info(
                "%s %s -> %s in %.1fms cost=%s remaining=%s",
                method,
                self._safe_path(url),
                response.status_code,
                elapsed_ms,
                response.headers.get("X-Request-Cost") or response.headers.get("x-request-cost"),
                response.headers.get("X-Rate-Limit-Remaining")
                or response.headers.get("x-rate-limit-remaining"),
            )

            if is_throttle_response(response.status_code, response.headers, response.text):
                if attempt >= self._max_retries:
                    raise CanvasRateLimitError(
                        "Canvas kept throttling requests after bounded retries. Try again in a moment."
                    )
                await self._sleep(get_retry_delay(attempt, response.headers))
                continue

            if response.status_code >= 400:
                raise CanvasResponseError(response.status_code, self._error_message(response))

            budget_delay = get_budget_delay(response.headers)
            if budget_delay > 0:
                await self._sleep(budget_delay)

            return response

        raise CanvasRateLimitError("Canvas request retries were exhausted.")

    @staticmethod
    def _error_message(response: HttpResponse) -> str:
        try:
            payload = response.json()
        except Exception:
            payload = None

        if isinstance(payload, dict):
            errors = payload.get("errors")
            if isinstance(errors, list) and errors:
                first = errors[0]
                if isinstance(first, dict):
                    message = first.get("message")
                    if isinstance(message, str) and message.strip():
                        return message.strip()
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()

        if response.status_code == 401:
            return "Authentication failed. Check CANVAS_TOKEN and Canvas base URL."
        if response.status_code == 404:
            return "The requested Canvas resource was not found."
        return "Canvas returned an unexpected error."

    async def _get_paginated(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        current_url: str | None = self._make_url(path)
        current_params: Mapping[str, Any] | None = {"per_page": 100, **(params or {})}
        results: list[dict[str, Any]] = []

        while current_url is not None:
            response = await self._request("GET", current_url, params=current_params)
            payload = response.json()
            if not isinstance(payload, list):
                raise CanvasResponseError(response.status_code, "Canvas returned a non-list payload.")

            results.extend(item for item in payload if isinstance(item, dict))
            current_url = get_next_link(response.headers)
            current_params = None

        return results

    async def list_courses(self) -> list[Course]:
        payloads = await self._get_paginated(
            "/api/v1/courses",
            params={"enrollment_type": "student", "state[]": "available"},
        )
        courses = [Course.from_payload(payload) for payload in payloads]
        return [course for course in courses if course.workflow_state != "deleted"]

    async def list_course_files(
        self,
        course_id: int,
        search: str | None = None,
    ) -> list[CanvasFile]:
        params: dict[str, Any] = {}
        if search:
            params["search_term"] = search
        payloads = await self._get_paginated(f"/api/v1/courses/{course_id}/files", params=params)
        return [CanvasFile.from_payload(payload) for payload in payloads]

    async def get_file(self, file_id: int) -> CanvasFile:
        response = await self._request("GET", f"/api/v1/files/{file_id}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise CanvasResponseError(response.status_code, "Canvas returned invalid file metadata.")
        return CanvasFile.from_payload(payload)

    async def download_file(self, canvas_file: CanvasFile) -> bytes:
        if not canvas_file.url:
            raise CanvasResponseError(400, f"File {canvas_file.id} does not include a download URL.")

        response = await self._request("GET", canvas_file.url)
        return bytes(response.content)

    async def list_modules(self, course_id: int) -> list[CanvasModule]:
        payloads = await self._get_paginated(f"/api/v1/courses/{course_id}/modules")
        return [CanvasModule.from_payload(payload) for payload in payloads]

    async def list_module_items(
        self,
        course_id: int,
        module_id: int,
    ) -> list[CanvasModuleItem]:
        payloads = await self._get_paginated(
            f"/api/v1/courses/{course_id}/modules/{module_id}/items"
        )
        return [CanvasModuleItem.from_payload(payload, module_id) for payload in payloads]

    async def list_assignments(self, course_id: int) -> list[CanvasAssignment]:
        payloads = await self._get_paginated(f"/api/v1/courses/{course_id}/assignments")
        return [CanvasAssignment.from_payload(payload) for payload in payloads]

    async def list_announcements(
        self,
        course_id: int | None = None,
        limit: int = 5,
    ) -> list[CanvasAnnouncement]:
        params: dict[str, Any] = {}
        if course_id is not None:
            params["context_codes[]"] = f"course_{course_id}"
        payloads = await self._get_paginated("/api/v1/announcements", params=params)
        announcements = [CanvasAnnouncement.from_payload(payload) for payload in payloads]
        return announcements[:limit]
