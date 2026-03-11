from research_assistant_api.mcp.cli import main


def test_mcp_cli_runs_with_default_stdio(monkeypatch):
    captured: dict[str, object] = {}

    class DummyServer:
        def run(self, transport: str = "stdio", mount_path: str | None = None) -> None:
            captured["transport"] = transport
            captured["mount_path"] = mount_path

    def fake_create_mcp_server(settings):
        captured["settings"] = settings
        return DummyServer()

    monkeypatch.setattr(
        "research_assistant_api.mcp.cli.create_mcp_server",
        fake_create_mcp_server,
    )

    exit_code = main([])

    assert exit_code == 0
    assert captured["transport"] == "stdio"
    assert captured["mount_path"] == captured["settings"].mcp_mount_path


def test_mcp_cli_supports_mount_path_override(monkeypatch):
    captured: dict[str, object] = {}

    class DummyServer:
        def run(self, transport: str = "stdio", mount_path: str | None = None) -> None:
            captured["transport"] = transport
            captured["mount_path"] = mount_path

    def fake_create_mcp_server(settings):
        return DummyServer()

    monkeypatch.setattr(
        "research_assistant_api.mcp.cli.create_mcp_server",
        fake_create_mcp_server,
    )

    exit_code = main(["--transport", "streamable-http", "--mount-path", "/mcp-alt"])

    assert exit_code == 0
    assert captured["transport"] == "streamable-http"
    assert captured["mount_path"] == "/mcp-alt"
