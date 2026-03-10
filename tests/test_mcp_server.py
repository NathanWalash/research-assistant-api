import pytest

from research_assistant_api.mcp.server import create_mcp_server


@pytest.mark.anyio
async def test_mcp_server_exposes_health_tool() -> None:
    server = create_mcp_server()
    tools = await server.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "health_check" in tool_names


@pytest.mark.anyio
async def test_mcp_health_tool_returns_ok_payload() -> None:
    server = create_mcp_server()
    _content, payload = await server.call_tool("health_check", {})

    assert payload == {"service": "research-assistant-api", "status": "ok"}
