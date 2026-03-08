# Research Assistant API

Research Assistant API is a FastAPI service for discovering and organising scholarly research data derived from OpenAlex.

## Current Status

The repository currently contains the raw Leeds articles CSV and the initial application scaffold. The first development batch focuses on:

- FastAPI service setup
- database foundation
- initial relational schema
- smoke tests

## Local Development

1. Copy `.env.example` to `.env`.
2. Start PostgreSQL with `docker compose up -d db`.
3. Install dependencies with `python -m pip install -e .[dev]`.
4. Run the API with `uvicorn research_assistant_api.main:app --reload`.

The default database configuration uses PostgreSQL with the `pgvector` image so vector support can be added later without replacing the local database container. The container is published on `localhost:5433` to avoid clashing with an existing PostgreSQL service on the default `5432` port.

## Testing

Run the smoke test suite with:

```bash
python -m pytest
```

The current tests cover:

- application startup
- health endpoint response
- SQLAlchemy session connectivity
- Alembic migration wiring against SQLite
- CSV ingestion for papers, topics, authors, institutions, and optional citation edges

## Continuous Integration

GitHub Actions is configured in `.github/workflows/ci.yml`.

The workflow currently runs:

- the Python smoke test suite on every push and pull request
- an Alembic migration check against PostgreSQL using a `pgvector` service container

## Data Ingestion

Import the main Leeds/OpenAlex-derived CSV with:

```bash
research-assistant-ingest
```

Useful options:

- `research-assistant-ingest --limit 100`
- `research-assistant-ingest --csv-path path/to/data.csv`
- `research-assistant-ingest --citation-csv-path path/to/citation_edges.csv`

The current Leeds CSV includes:

- papers
- topics
- authors
- institutions
- citation counts

It does not include citation edge pairs in the main file, so citation neighbourhood data requires a supplementary CSV with `citing_paper_id` and `cited_paper_id` columns.

## Planned Capabilities

- paper discovery and metadata lookup
- citation graph exploration
- semantic similarity and recommendations
- project, reading list, and annotation workflows
- research analytics endpoints
