# MCP Usage

This repository includes a read-only MCP server surface for public discovery and
analytics operations.

Protected user routes (auth, projects, reading lists, annotations) are not
exposed through MCP.

## Local STDIO

Run MCP in local stdio mode:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.mcp.cli --transport stdio
```

Equivalent script entrypoint:

```bash
research-assistant-mcp --transport stdio
```

## Local Streamable HTTP

Enable MCP mount in FastAPI:

```bash
$env:RESEARCH_API_MCP_ENABLED="true"
$env:RESEARCH_API_MCP_MOUNT_PATH="/mcp"
.\.venv\Scripts\python.exe -m uvicorn research_assistant_api.main:app --reload
```

MCP streamable HTTP will be mounted at:

- `http://127.0.0.1:8000/mcp`

## Tool Inventory

### Health

- `health_check`

### Papers

- `papers_search`
- `papers_get`
- `papers_similar`
- `papers_citations`
- `papers_path`

### Authors

- `authors_list`
- `authors_search`
- `authors_get`
- `authors_papers`

### Topics

- `topics_list`
- `topics_papers`

### Analytics

- `analytics_top_papers`
- `analytics_topics`
- `analytics_trends`
