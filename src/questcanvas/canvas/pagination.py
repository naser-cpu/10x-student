"""Helpers for Canvas pagination headers."""

from __future__ import annotations

import re
from collections.abc import Mapping

LINK_RE = re.compile(r'<([^>]+)>;\s*rel="([^"]+)"')


def parse_link_header(value: str | None) -> dict[str, str]:
    """Parse a RFC 5988 Link header into a relation map."""

    if not value:
        return {}

    relations: dict[str, str] = {}
    for url, relation in LINK_RE.findall(value):
        relations[relation] = url
    return relations


def get_next_link(headers: Mapping[str, str]) -> str | None:
    """Return the next pagination URL, if present."""

    link_value = headers.get("Link") or headers.get("link")
    return parse_link_header(link_value).get("next")
