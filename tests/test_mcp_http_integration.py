import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


def _pick_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_health(url: str, timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1) as response:  # nosec: B310
                if response.status == 200:
                    return
        except (TimeoutError, URLError):
            time.sleep(0.2)
    raise RuntimeError(f"Server did not become healthy within {timeout_seconds} seconds")


@pytest.mark.anyio
async def test_mcp_http_end_to_end_over_fastapi_mount() -> None:
    port = _pick_free_port()
    repo_root = Path(__file__).resolve().parents[1]

    environment = os.environ.copy()
    environment["RESEARCH_API_ENVIRONMENT"] = "test"
    environment["RESEARCH_API_DATABASE_URL"] = (
        "sqlite+pysqlite:///file:mcp_http_integration?"
        "mode=memory&cache=shared&uri=true"
    )
    environment["RESEARCH_API_JWT_SECRET_KEY"] = "test-secret-key-with-32-byte-minimum"
    environment["RESEARCH_API_MCP_ENABLED"] = "true"
    environment["RESEARCH_API_MCP_MOUNT_PATH"] = "/mcp"

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "research_assistant_api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    process = subprocess.Popen(
        command,
        cwd=str(repo_root),
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        _wait_for_health(f"http://127.0.0.1:{port}/health")

        async with streamable_http_client(
            f"http://127.0.0.1:{port}/mcp"
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                initialize_result = await session.initialize()
                assert initialize_result.serverInfo.name

                tools = await session.list_tools()
                tool_names = {tool.name for tool in tools.tools}
                assert "health_check" in tool_names
                assert "papers_search" in tool_names

                result = await session.call_tool("health_check", {})
                assert result.structuredContent == {
                    "service": "research-assistant-api",
                    "status": "ok",
                }
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
