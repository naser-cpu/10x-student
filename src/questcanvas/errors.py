"""Shared application errors."""

from __future__ import annotations


class QuestCanvasError(Exception):
    """Base error for QuestCanvas."""


class ConfigError(QuestCanvasError):
    """Raised when application configuration is invalid."""


class CanvasClientError(QuestCanvasError):
    """Raised when Canvas API access fails."""


class CanvasResponseError(CanvasClientError):
    """Raised when Canvas returns an unexpected response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Canvas request failed with status {status_code}: {message}")
        self.status_code = status_code
        self.message = message


class CanvasRateLimitError(CanvasClientError):
    """Raised when Canvas keeps throttling after bounded retries."""


class ExtractionError(QuestCanvasError):
    """Raised when file extraction fails."""


class UnsupportedFileTypeError(ExtractionError):
    """Raised when a file type is not supported for extraction."""


class MissingDependencyError(QuestCanvasError):
    """Raised when an optional runtime dependency is unavailable."""
