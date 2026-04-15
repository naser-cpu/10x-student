"""Authentication abstractions for Canvas access."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from .errors import ConfigError


class TokenProvider(Protocol):
    """Provides a Canvas access token."""

    async def get_token(self) -> str:
        """Return a usable Canvas token."""


@dataclass(slots=True)
class EnvTokenProvider:
    """Reads a Canvas PAT from an environment variable."""

    env_var: str = "CANVAS_TOKEN"

    async def get_token(self) -> str:
        token = os.getenv(self.env_var, "").strip()
        if not token:
            raise ConfigError(
                f"Missing {self.env_var}. Set a Canvas personal access token before starting QuestCanvas."
            )
        return token


@dataclass(slots=True)
class StaticTokenProvider:
    """Provides an already validated token."""

    token: str

    async def get_token(self) -> str:
        if not self.token.strip():
            raise ConfigError("Canvas token is empty.")
        return self.token
