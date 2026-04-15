from __future__ import annotations

import unittest

from questcanvas.auth import EnvTokenProvider, StaticTokenProvider
from questcanvas.config import AppConfig, normalize_base_url
from questcanvas.errors import ConfigError


class ConfigTests(unittest.IsolatedAsyncioTestCase):
    def test_normalize_base_url_strips_trailing_slash(self) -> None:
        self.assertEqual(
            normalize_base_url("https://canvas.example.edu/"),
            "https://canvas.example.edu",
        )

    def test_invalid_base_url_fails(self) -> None:
        with self.assertRaises(ConfigError):
            normalize_base_url("not a url")

    def test_missing_env_fails_fast(self) -> None:
        with self.assertRaises(ConfigError):
            AppConfig.from_env({})

    async def test_token_providers(self) -> None:
        token = await StaticTokenProvider("abc123").get_token()
        self.assertEqual(token, "abc123")

        provider = EnvTokenProvider(env_var="MISSING_QUESTCANVAS_TOKEN")
        with self.assertRaises(ConfigError):
            await provider.get_token()
