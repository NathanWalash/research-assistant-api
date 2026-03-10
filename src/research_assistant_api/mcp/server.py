from mcp.server.fastmcp import FastMCP

from research_assistant_api.core.config import Settings, get_settings
from research_assistant_api.db.session import get_session_factory
from research_assistant_api.mcp.tools_public import register_public_tools


def create_mcp_server(settings: Settings | None = None) -> FastMCP:
    resolved_settings = settings or get_settings()
    mcp = FastMCP(
        name=resolved_settings.mcp_name,
        instructions=(
            "Read-only MCP tools for scholarly discovery and analytics over the "
            "Leeds OpenAlex subset."
        ),
        host=resolved_settings.mcp_host,
        port=resolved_settings.mcp_port,
        # When mounted under FastAPI, the app should expose streamable HTTP at root.
        streamable_http_path="/",
    )

    @mcp.tool(
        name="health_check",
        description="Return a simple health payload for MCP smoke checks.",
    )
    def health_check() -> dict[str, str]:
        return {"service": "research-assistant-api", "status": "ok"}

    register_public_tools(
        mcp,
        session_factory=get_session_factory(resolved_settings.database_url),
    )

    return mcp
