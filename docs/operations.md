# Operations

## Ingestion

Main dataset import:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.ingestion.cli
```

Useful options:

- `--limit 100`
- `--csv-path path/to/file.csv`
- `--citation-csv-path data/derived/leeds_citation_edges.csv`

Operational notes:

- ingestion is idempotent for existing keys and safe to rerun
- malformed rows are skipped and counted in the CLI summary
- citation edges referencing missing papers are skipped to preserve relational integrity

## Embeddings

Generate missing embeddings:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.embeddings.cli
```

Regenerate all embeddings:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.embeddings.cli --force
```

The CLI prints batch progress as `Embedded X/Y papers`.

Useful options:

- `--paper-id https://openalex.org/W123`
- `--limit 500`
- `--force`

## Citation Graph Export

Run the resumable export:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.citation_graph.cli --rate-interval 0.2
```

Reset the export state:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.citation_graph.cli --reset
```

Default progress/output files:

- `.tmp/leeds_citation_queries.csv`
- `.tmp/leeds_citation_works.jsonl`
- `.tmp/leeds_citation_edges.csv`
- `.tmp/leeds_citation_progress.json`

Operational notes:

- rerunning without `--reset` resumes from progress state
- `--reset` discards partial progress and restarts export from scratch
- edge CSV can be reimported via ingestion CLI using `--citation-csv-path`

## Quality Checks

Primary local quality gates:

```bash
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest
```

Targeted checks:

```bash
.\.venv\Scripts\python.exe -m pytest tests/test_api_coverage_api.py
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_http_integration.py
.\.venv\Scripts\python.exe -m pytest tests/test_postgres_integration.py
```

Note: `tests/test_postgres_integration.py` requires PostgreSQL with pgvector and is skipped in SQLite-only runs.

## Container Workflow

Start the full local stack:

```bash
docker compose --profile app up -d --build
```

Inspect logs:

```bash
docker compose --profile app logs api --tail 100
```

Stop the stack:

```bash
docker compose --profile app down -v
```

## Database Snapshot Workflow (Recommended For Deployment)

If you already populated local Postgres (ingestion + embeddings + citation edges), use snapshot/restore instead of rerunning heavy pipelines in hosted shells.

### 1) Export a local data snapshot

From host machine with `pg_dump`:

```bash
pg_dump --data-only --no-owner --no-privileges --format=custom --file artifacts/research_assistant_data.dump "postgresql://research_user:research_password@localhost:5433/research_assistant"
```

Or from Dockerized Postgres:

```bash
docker compose exec -T db pg_dump --data-only --no-owner --no-privileges --format=custom \
  --file /tmp/research_assistant_data.dump -U research_user -d research_assistant
docker compose cp db:/tmp/research_assistant_data.dump artifacts/research_assistant_data.dump
```

### 2) Restore into target database

Run migrations first on the target (schema must exist), then restore data:

```bash
pg_restore --data-only --no-owner --no-privileges --dbname "$RAILWAY_DATABASE_URL" artifacts/research_assistant_data.dump
```

### 3) Verify

- `GET /health`
- `GET /papers/search`
- `GET /papers/{id}/similar`
- `GET /projects/{id}/recommendations` (after creating a project and adding context papers)
