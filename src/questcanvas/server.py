"""QuestCanvas application assembly and MCP server adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .auth import StaticTokenProvider, TokenProvider
from .canvas.client import CanvasClient
from .config import AppConfig
from .errors import MissingDependencyError
from .services.files import FileService
from .tools.announcements import handle_list_announcements
from .tools.assignments import handle_list_assignments
from .tools.courses import handle_list_courses
from .tools.files import handle_get_file_text, handle_list_course_files
from .tools.modules import handle_list_modules


@dataclass(slots=True)
class QuestCanvasApp:
    """Assembles configuration, services, and tool handlers."""

    config: AppConfig
    token_provider: TokenProvider
    canvas_client: CanvasClient
    file_service: FileService

    @classmethod
    def from_env(cls) -> "QuestCanvasApp":
        config = AppConfig.from_env()
        config.ensure_data_dir()
        token_provider = StaticTokenProvider(config.canvas_token)
        canvas_client = CanvasClient(config.canvas_base_url, token_provider)
        file_service = FileService(canvas_client)
        return cls(
            config=config,
            token_provider=token_provider,
            canvas_client=canvas_client,
            file_service=file_service,
        )

    async def aclose(self) -> None:
        await self.canvas_client.aclose()

    async def list_courses(self) -> list[dict[str, Any]]:
        return await handle_list_courses(self.canvas_client)

    async def list_course_files(
        self,
        course_id: int,
        module_id: int | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        return await handle_list_course_files(
            self.file_service,
            course_id,
            module_id=module_id,
            search=search,
        )

    async def list_modules(self, course_id: int) -> list[dict[str, Any]]:
        return await handle_list_modules(self.canvas_client, course_id)

    async def get_file_text(self, file_id: int, max_units: int = 40) -> dict[str, Any]:
        return await handle_get_file_text(self.file_service, file_id, max_units=max_units)

    async def get_assignments(self, course_id: int) -> list[dict[str, Any]]:
        return await handle_list_assignments(self.canvas_client, course_id)

    async def get_announcements(
        self,
        course_id: int | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return await handle_list_announcements(self.canvas_client, course_id=course_id, limit=limit)

    def build_mcp_server(self) -> Any:
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError as exc:
            raise MissingDependencyError(
                "The Python MCP SDK is required to run the stdio server. Install project dependencies first."
            ) from exc

        server = FastMCP("QuestCanvas")

        @server.tool()
        async def list_courses() -> list[dict[str, Any]]:
            return await self.list_courses()

        @server.tool()
        async def list_course_files(
            course_id: int,
            module_id: int | None = None,
            search: str | None = None,
        ) -> list[dict[str, Any]]:
            return await self.list_course_files(course_id, module_id=module_id, search=search)

        @server.tool()
        async def list_modules(course_id: int) -> list[dict[str, Any]]:
            return await self.list_modules(course_id)

        @server.tool()
        async def get_file_text(file_id: int, max_units: int = 40) -> dict[str, Any]:
            return await self.get_file_text(file_id, max_units=max_units)

        @server.tool()
        async def get_assignments(course_id: int) -> list[dict[str, Any]]:
            return await self.get_assignments(course_id)

        @server.tool()
        async def get_announcements(
            course_id: int | None = None,
            limit: int = 5,
        ) -> list[dict[str, Any]]:
            return await self.get_announcements(course_id=course_id, limit=limit)

        return server

    def run_stdio(self) -> None:
        server = self.build_mcp_server()
        server.run()
