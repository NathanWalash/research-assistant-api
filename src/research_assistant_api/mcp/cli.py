import argparse
from typing import Sequence

from research_assistant_api.core.config import get_settings
from research_assistant_api.mcp.server import create_mcp_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Research Assistant MCP server.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="MCP transport to run.",
    )
    parser.add_argument(
        "--mount-path",
        default=None,
        help="Override streamable HTTP mount path.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    server = create_mcp_server(settings)
    mount_path = args.mount_path or settings.mcp_mount_path
    server.run(transport=args.transport, mount_path=mount_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
