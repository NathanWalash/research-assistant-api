from pathlib import Path

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.mcp.server import create_mcp_server

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _seed_dataset(database_url: str) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds.csv",
        citation_csv_path=FIXTURES_DIR / "sample_citation_edges.csv",
        batch_size=10,
    )

    with session_factory() as session:
        CsvIngestionService(session).ingest(config)


@pytest.fixture
def mcp_server(sqlite_database_url: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "RESEARCH_API_JWT_SECRET_KEY",
        "test-secret-key-with-32-byte-minimum",
    )
    _seed_dataset(sqlite_database_url)
    return create_mcp_server()


async def _call_tool(server, name: str, arguments: dict):
    _content, payload = await server.call_tool(name, arguments)
    if isinstance(payload, dict) and "result" in payload:
        return payload["result"]
    return payload


@pytest.mark.anyio
async def test_mcp_public_tool_inventory(mcp_server) -> None:
    tools = await mcp_server.list_tools()
    tool_names = {tool.name for tool in tools}

    assert {
        "health_check",
        "papers_search",
        "papers_get",
        "papers_similar",
        "papers_citations",
        "papers_path",
        "authors_list",
        "authors_search",
        "authors_get",
        "authors_papers",
        "topics_list",
        "topics_papers",
        "analytics_top_papers",
        "analytics_topics",
        "analytics_trends",
    }.issubset(tool_names)
    assert "auth_login" not in tool_names
    assert "projects_list" not in tool_names


@pytest.mark.anyio
async def test_mcp_public_tools_return_expected_payloads(mcp_server) -> None:
    search_payload = await _call_tool(
        mcp_server,
        "papers_search",
        {"limit": 2, "offset": 0},
    )
    assert search_payload
    first_paper_id = search_payload[0]["id"]

    paper_payload = await _call_tool(
        mcp_server,
        "papers_get",
        {"paper_id": first_paper_id},
    )
    assert paper_payload["id"] == first_paper_id

    author_payload = await _call_tool(
        mcp_server,
        "authors_search",
        {"query": "alice", "limit": 5, "offset": 0},
    )
    assert author_payload
    assert "alice" in author_payload[0]["name"].lower()

    topics_payload = await _call_tool(
        mcp_server,
        "topics_list",
        {"limit": 10, "offset": 0},
    )
    assert topics_payload

    analytics_payload = await _call_tool(
        mcp_server,
        "analytics_top_papers",
        {"limit": 5, "offset": 0},
    )
    assert analytics_payload


@pytest.mark.anyio
async def test_mcp_citation_tools_use_local_graph(mcp_server) -> None:
    neighborhood_payload = await _call_tool(
        mcp_server,
        "papers_citations",
        {"paper_id": "https://openalex.org/W1", "limit": 20, "offset": 0},
    )
    citing_ids = {paper["id"] for paper in neighborhood_payload["citing_papers"]}
    assert "https://openalex.org/W2" in citing_ids

    path_payload = await _call_tool(
        mcp_server,
        "papers_path",
        {
            "paper_id": "https://openalex.org/W2",
            "target_paper_id": "https://openalex.org/W1",
            "max_depth": 6,
        },
    )
    assert path_payload["path_length"] == 1
    assert [paper["id"] for paper in path_payload["path"]] == [
        "https://openalex.org/W2",
        "https://openalex.org/W1",
    ]


@pytest.mark.anyio
async def test_mcp_public_tool_validation_returns_tool_error(mcp_server) -> None:
    with pytest.raises(ToolError):
        await mcp_server.call_tool("authors_search", {"query": "   "})

    with pytest.raises(ToolError):
        await mcp_server.call_tool("papers_search", {"limit": 0, "offset": 0})
