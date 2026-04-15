"""Canvas rate limit helpers."""

from __future__ import annotations

from collections.abc import Mapping


def parse_float_header(headers: Mapping[str, str], key: str) -> float | None:
    """Parse a float-like header value."""

    raw_value = headers.get(key) or headers.get(key.lower())
    if raw_value is None:
        return None

    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def is_throttle_response(status_code: int, headers: Mapping[str, str], body_text: str) -> bool:
    """Return whether the response looks like Canvas throttling."""

    if status_code == 429:
        return True
    if status_code != 403:
        return False

    lowered = body_text.lower()
    return "rate limit" in lowered or "throttle" in lowered or "too many requests" in lowered


def get_retry_delay(attempt: int, headers: Mapping[str, str]) -> float:
    """Return a bounded retry delay for rate-limited requests."""

    retry_after = headers.get("Retry-After") or headers.get("retry-after")
    if retry_after:
        try:
            return max(0.0, min(float(retry_after), 8.0))
        except ValueError:
            pass

    return min(0.5 * (2**attempt), 8.0)


def get_budget_delay(headers: Mapping[str, str]) -> float:
    """Add a small pause when the Canvas budget is running low."""

    remaining = parse_float_header(headers, "X-Rate-Limit-Remaining")
    if remaining is None:
        return 0.0
    if remaining <= 0.2:
        return 1.0
    if remaining <= 1.0:
        return 0.5
    return 0.0
