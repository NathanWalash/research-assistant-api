import pytest
from fastapi.testclient import TestClient

from research_assistant_api.main import create_app


def _mounted_paths(app) -> set[str]:
    return {
        route.path
        for route in app.routes
        if hasattr(route, "app") and hasattr(route, "path")
    }


def test_mcp_mount_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RESEARCH_API_MCP_ENABLED", raising=False)
    app = create_app()

    assert "/mcp" not in _mounted_paths(app)
    client = TestClient(app)
    response = client.get("/mcp")
    assert response.status_code == 404


def test_mcp_mount_is_enabled_with_env_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RESEARCH_API_MCP_ENABLED", "true")
    monkeypatch.setenv("RESEARCH_API_MCP_MOUNT_PATH", "/mcp")
    app = create_app()

    assert "/mcp" in _mounted_paths(app)


def test_mcp_mount_respects_custom_mount_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RESEARCH_API_MCP_ENABLED", "true")
    monkeypatch.setenv("RESEARCH_API_MCP_MOUNT_PATH", "mcp-alt")
    app = create_app()
    mounted_paths = _mounted_paths(app)

    assert "/mcp-alt" in mounted_paths
