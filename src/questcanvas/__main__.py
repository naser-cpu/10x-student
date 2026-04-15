"""CLI entry point for the local QuestCanvas MCP server."""

from __future__ import annotations

from .server import QuestCanvasApp


def main() -> None:
    app = QuestCanvasApp.from_env()
    app.run_stdio()


if __name__ == "__main__":
    main()
