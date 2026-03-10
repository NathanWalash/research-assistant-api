from mcp.server.fastmcp import FastMCP

from research_assistant_api.core.config import Settings, get_settings


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
        streamable_http_path=resolved_settings.mcp_mount_path,
    )

    @mcp.tool(
        name="health_check",
        description="Return a simple health payload for MCP smoke checks.",
    )
    def health_check() -> dict[str, str]:
        return {"service": "research-assistant-api", "status": "ok"}

    return mcp
