import os

import httpx
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("TrueSource")

API_URL = os.getenv("TRUESOURCE_API_URL", "http://localhost:8000")


async def backend_get(path: str):
    """Fetch a read-only resource from the TrueSource control plane.

    Do not write log messages to stdout here: stdio is the MCP protocol channel.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}{path}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"TrueSource API request failed for {path}: {exc}") from exc


@mcp.tool()
async def get_verified_knowledge() -> dict:
    """Return the enterprise facts that TrueSource
    has verified."""
    return await backend_get("/api/knowledge")


@mcp.tool()
async def list_drift_incidents() -> list[dict]:
    """List detected documentation-drift
    incidents."""
    return await backend_get("/api/drift")


@mcp.tool()
async def get_document_status() -> list[dict]:
    """List enterprise documents and whether they
    are verified or stale."""
    return await backend_get("/api/documents")


if __name__ == "__main__":
    mcp.run(transport="stdio")
