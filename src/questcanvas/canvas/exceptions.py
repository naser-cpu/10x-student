"""Compatibility re-exports for Canvas-specific errors."""

from ..errors import CanvasClientError, CanvasRateLimitError, CanvasResponseError

__all__ = ["CanvasClientError", "CanvasRateLimitError", "CanvasResponseError"]
