# Research Assistant API

Research Assistant API is a production-style FastAPI backend (plus a browser frontend at `/app`) for scholarly discovery and research workflow management on an OpenAlex-derived Leeds corpus.

The system combines relational search, vector similarity, citation-subgraph traversal, user workspaces, and deployment-grade CI/CD.

## Documentation Map

- [Getting Started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)
- [API Examples](docs/api-examples.md)
- [Endpoint Test Coverage](docs/endpoint-test-coverage.md)
- [MCP Usage](docs/mcp-usage.md)
- [Operations](docs/operations.md)
- [Railway Deployment](docs/railway-deployment.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Demo Flow](docs/demo-flow.md)

## Delivered Scope

- paper discovery, paper detail, topic and author exploration
- vector-based similar-paper retrieval with pgvector
- citation neighbourhood and shortest-path traversal on a Leeds-only citation subgraph
- corpus analytics endpoints (top papers, topics, yearly trends)
- JWT auth (`register`, `login`, `me`)
- protected project, reading-list, and annotation workflows
- configurable recommendation scoring (`semantic`, `citation`, `hybrid`)
- MCP read-only tools for public discovery and analytics
- React frontend served by FastAPI at `/app`
- Dockerized runtime and Railway deployment configuration

## Stack And Justification

| Layer | Choice | Why |
| --- | --- | --- |
| API framework | FastAPI | Strong schema validation, OpenAPI generation, clean dependency injection, async-ready architecture |
| ORM + migrations | SQLAlchemy 2 + Alembic | Explicit domain model, deterministic migration history, test/runtime parity |
| Database | PostgreSQL 16 | Reliable relational semantics and efficient filtering/joins for scholarly metadata |
| Vector search | pgvector | Co-locates embeddings with metadata and avoids introducing a separate vector datastore |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Good quality/performance tradeoff for local reproducible batch embedding |
| Auth | JWT bearer tokens | Stateless API auth with straightforward frontend integration |
| Frontend | React + esbuild | Lightweight build with explicit API interaction and low deployment complexity |
| CI/CD | GitHub Actions + Docker + Railway | Repeatable quality gates and one-click cloud deploy path |

## Data Model And Storage Strategy

Core scholarly entities:

- `papers`
- `authors`
- `institutions`
- `topics`
- `paper_authors`
- `citations`

User workflow entities:

- `users`
- `projects`
- `reading_list_items`
- `annotations`

Storage decisions:

- embeddings are stored on `papers.embedding` (pgvector)
- citation edges are explicit directed pairs (`citing_paper_id -> cited_paper_id`)
- SQLite is used only for lightweight test runs with Python cosine fallback logic

## API Surface

Public discovery/analytics:

- `GET /health`
- `GET /papers/search`
- `GET /papers/{paper_id}`
- `GET /papers/{paper_id}/similar`
- `GET /papers/{paper_id}/citations`
- `GET /papers/{paper_id}/path/{target_paper_id}`
- `GET /authors`
- `GET /authors/search`
- `GET /authors/{author_id}`
- `GET /authors/{author_id}/papers`
- `GET /topics`
- `GET /topics/{topic_id}/papers`
- `GET /analytics/top-papers`
- `GET /analytics/topics`
- `GET /analytics/trends`

Authenticated:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /papers/{paper_id}/annotations`
- `GET /papers/{paper_id}/annotations`
- `GET /annotations/{annotation_id}`
- `PATCH /annotations/{annotation_id}`
- `DELETE /annotations/{annotation_id}`
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `DELETE /projects/{project_id}`
- `GET /projects/{project_id}/recommendations`
- `POST /projects/{project_id}/reading-list`
- `GET /projects/{project_id}/reading-list`
- `PATCH /reading-list-items/{item_id}`
- `DELETE /reading-list-items/{item_id}`

Removed by design:

- `GET /analytics/collaborations` (removed due to poor interactive performance at this dataset size)

## Pipeline Design

### 1) CSV Ingestion Pipeline

Command:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.ingestion.cli
```

Role:

- parses OpenAlex CSV rows
- upserts papers/authors/institutions/topics/authorship links
- optionally imports citation edges from a dedicated edge CSV
- skips malformed rows and reports skip counts instead of failing the full run
- prints live batch progress with processed rows, skipped rows, elapsed time, and ETA

Time complexity:

- `O(N + E)` where `N` is source metadata rows and `E` is optional citation-edge rows

### 2) Embedding Pipeline

Command:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.embeddings.cli
```

Role:

- builds embedding text from `title + abstract` (title-only fallback if abstract missing)
- computes vectors in batches
- writes vectors to `papers.embedding`
- supports incremental mode (missing only) and `--force` re-embed mode
- prints incremental progress with processed count, percentage, elapsed time, and ETA

Approximate complexity:

- model inference dominates runtime: `O(N * d)` for `N` papers and embedding dimension `d` (384 for MiniLM-L6-v2), plus DB write cost

### 3) Citation Graph Export Pipeline

Command:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.citation_graph.cli --rate-interval 0.2
```

Role:

- queries OpenAlex in Leeds-ID batches
- persists progress checkpoints for resumability
- writes Leeds-to-Leeds edge pairs
- exports a usable `citing_paper_id,cited_paper_id` CSV

Outputs:

- `.tmp/leeds_citation_queries.csv`
- `.tmp/leeds_citation_works.jsonl`
- `.tmp/leeds_citation_edges.csv`
- `.tmp/leeds_citation_progress.json`

Approximate complexity:

- network-bound `O(B * R)` where `B` is batch count and `R` is remote page retrieval cost

### 4) Recommendation Algorithm

Endpoint:

- `GET /projects/{project_id}/recommendations`

Modes:

- `semantic`
- `citation`
- `hybrid` (default)

Default hybrid score:

```text
score = 0.7 * semantic_similarity + 0.3 * citation_signal
```

Complexity sketch:

- semantic ranking roughly scales with `O(C * K)` for candidate count `C` and reading-list context size `K`
- citation signal is derived from direct citation-neighbour relationships in the local subgraph

## Dataset Constraints And Honest Scope

The primary Leeds metadata CSV contains citation counts (`cited_by_count`) but not full citation-edge pairs. Therefore:

- metadata analytics can use citation counts immediately
- traversal endpoints require supplemental edge ingestion
- resulting graph coverage is complete only inside the Leeds subset

This is intentional and explicitly documented in this repo and API behavior.

## Local Development

1. Copy `.env.example` to `.env`.
2. Start database:
```bash
docker compose up -d db
```
3. Create + activate virtualenv:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
4. Install:
```bash
python -m pip install -e ".[dev]"
```
5. Run migrations:
```bash
.\.venv\Scripts\python.exe -m alembic upgrade head
```
6. Ingest dataset:
```bash
.\.venv\Scripts\python.exe -m research_assistant_api.ingestion.cli
```
7. Generate embeddings:
```bash
.\.venv\Scripts\python.exe -m research_assistant_api.embeddings.cli
```
8. Start API:
```bash
.\.venv\Scripts\python.exe -m uvicorn research_assistant_api.main:app --reload
```

Endpoints:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8000/app`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

Optional MCP:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.mcp.cli --transport stdio
```

## Test Strategy

Main commands:

```bash
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest
```

What is validated:

- API contract inventory and validation edge cases
- auth and authorization boundaries
- discovery, similarity, citation, analytics behavior
- project/reading-list/annotation ownership rules
- recommendation ranking modes and weight handling
- ingestion, embedding, and citation-export CLI behavior
- MCP tool registry and HTTP mount integration
- PostgreSQL integration checks (including pgvector behavior)
- frontend smoke checks

Detailed endpoint-to-test mapping:

- [Endpoint Test Coverage Matrix](docs/endpoint-test-coverage.md)

## CI/CD Quality Gates

GitHub Actions (`.github/workflows/ci.yml`) includes:

- OpenAPI contract gate
- MCP contract gate (including mounted HTTP integration test)
- frontend build reproducibility gate
- full lint + pytest suite
- PostgreSQL migration and integration gate
- Docker smoke gate
- Docker MCP-mount smoke gate

## Deployment (Railway)

Railway deployment uses:

- root `Dockerfile`
- `railway.toml` healthcheck (`/health`)
- startup migration via `docker/entrypoint.sh` (`alembic upgrade head`)

Detailed steps:

- [Railway Deployment Guide](docs/railway-deployment.md)

## Fast Data Migration To Railway (No Pipeline Re-run)

Recommended production path after local pipelines complete:

1. Run ingestion + embeddings + citation-edge import locally once.
2. Export a PostgreSQL data snapshot from the local populated DB.
3. Deploy API + empty schema to Railway.
4. Restore snapshot into Railway Postgres.
5. Verify `/health`, `/papers/search`, `/papers/{id}/similar`, `/projects/{id}/recommendations`.

This avoids expensive re-computation in Railway runtime shells and is the fastest path to a fully seeded deployed environment.

Implementation details and commands are documented in:

- [Railway Deployment Guide](docs/railway-deployment.md)
- [Operations Guide](docs/operations.md)

## Notes On Branch History

Feature branches are intentionally retained to show staged development milestones and auditability.
