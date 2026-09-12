"""MCP client used by the TrueSource agent to execute read-only tools.

The OpenRouter model never connects to MCP directly.  This client owns the
stateful MCP session, translates discovered MCP tools to OpenAI-compatible
function schemas, and executes model-requested calls.
"""

from __future__ import annotations

import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClientError(RuntimeError):
    """Raised when the MCP server cannot safely satisfy a tool request."""


class TrueSourceMCPClient:
    """A short-lived, stateful client for the local TrueSource MCP server.

    Keep one instance open for a complete model/tool loop.  MCP sessions are
    stateful, so opening one session to discover tools and another to execute
    them is both wasteful and error-prone.
    """

    # Only expose non-mutating capabilities to the model.
    ALLOWED_TOOLS = frozenset(
        {
            "get_verified_knowledge",
            "list_drift_incidents",
            "get_document_status",
        }
    )

    def __init__(self) -> None:
        default_server = Path(__file__).resolve().parents[1] / "mcp" / "server.py"
        self.server_path = Path(os.getenv("MCP_SERVER_PATH", str(default_server))).resolve()
        self.command = os.getenv("MCP_SERVER_COMMAND", sys.executable)
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._available_tools: set[str] = set()

    async def __aenter__(self) -> "TrueSourceMCPClient":
        if not self.server_path.is_file():
            raise MCPClientError(f"MCP server was not found at {self.server_path}")

        self._stack = AsyncExitStack()
        try:
            read_stream, write_stream = await self._stack.enter_async_context(
                stdio_client(
                    StdioServerParameters(
                        command=self.command,
                        args=[str(self.server_path)],
                    )
                )
            )
            self._session = await self._stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self._session.initialize()
        except Exception as exc:
            await self._close()
            raise MCPClientError(f"Could not start the TrueSource MCP server: {exc}") from exc
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        await self._close()

    async def _close(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
        self._stack = None
        self._session = None
        self._available_tools.clear()

    def _require_session(self) -> ClientSession:
        if self._session is None:
            raise MCPClientError("Open the MCP client with 'async with' before using it")
        return self._session

    @staticmethod
    def _tool_schema(tool: Any) -> dict[str, Any]:
        """Translate an MCP Tool object into OpenAI/OpenRouter tool format."""
        input_schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
        if not input_schema:
            input_schema = {"type": "object", "properties": {}, "additionalProperties": False}
        if hasattr(input_schema, "model_dump"):
            input_schema = input_schema.model_dump(by_alias=True, mode="json")

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or f"Run the {tool.name} TrueSource tool.",
                "parameters": input_schema,
            },
        }

    async def openrouter_tools(self) -> list[dict[str, Any]]:
        """Discover the server's allowed tools as OpenRouter function schemas."""
        result = await self._require_session().list_tools()
        tools = [tool for tool in result.tools if tool.name in self.ALLOWED_TOOLS]
        self._available_tools = {tool.name for tool in tools}
        return [self._tool_schema(tool) for tool in tools]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Execute a discovered, allow-listed MCP tool and return JSON-safe data."""
        if name not in self.ALLOWED_TOOLS or name not in self._available_tools:
            raise MCPClientError(f"Tool '{name}' is not available to the TrueSource agent")
        if arguments is not None and not isinstance(arguments, dict):
            raise MCPClientError("MCP tool arguments must be a JSON object")

        try:
            result = await self._require_session().call_tool(name, arguments or {})
        except Exception as exc:
            raise MCPClientError(f"MCP tool '{name}' failed: {exc}") from exc

        if getattr(result, "is_error", getattr(result, "isError", False)):
            content = getattr(result, "content", [])
            raise MCPClientError(f"MCP tool '{name}' returned an error: {content}")

        structured_content = getattr(
            result, "structured_content", getattr(result, "structuredContent", None)
        )
        if structured_content is not None:
            return structured_content

        content = getattr(result, "content", [])
        return [
            item.model_dump(by_alias=True, mode="json") if hasattr(item, "model_dump") else item
            for item in content
        ]
