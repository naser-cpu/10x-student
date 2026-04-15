"""Application configuration loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from .errors import ConfigError

DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "questcanvas"


def normalize_base_url(raw_value: str) -> str:
    """Normalize the configured Canvas base URL."""

    value = raw_value.strip()
    if not value:
        raise ConfigError(
            "Missing CANVAS_BASE_URL. Set it to your Canvas root, for example https://canvas.example.edu."
        )

    parsed = urlparse(value)
    if not parsed.scheme:
        parsed = urlparse(f"https://{value}")

    if parsed.scheme not in {"http", "https"} or not parsed.netloc or " " in parsed.netloc:
        raise ConfigError(
            "CANVAS_BASE_URL must be a full http(s) URL like https://canvas.example.edu."
        )

    normalized_path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{normalized_path}"


@dataclass(slots=True)
class AppConfig:
    """Runtime configuration for the local MCP server."""

    canvas_base_url: str
    canvas_token: str
    data_dir: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AppConfig":
        values = dict(os.environ if env is None else env)
        canvas_base_url = normalize_base_url(values.get("CANVAS_BASE_URL", ""))
        canvas_token = values.get("CANVAS_TOKEN", "").strip()
        if not canvas_token:
            raise ConfigError(
                "Missing CANVAS_TOKEN. Set a Canvas personal access token before starting QuestCanvas."
            )

        data_dir_raw = values.get("QUESTCANVAS_DATA_DIR", "").strip()
        data_dir = Path(data_dir_raw).expanduser() if data_dir_raw else DEFAULT_DATA_DIR

        return cls(
            canvas_base_url=canvas_base_url,
            canvas_token=canvas_token,
            data_dir=data_dir,
        )

    def ensure_data_dir(self) -> Path:
        """Create the local data directory if needed."""

        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir
