# Research Assistant API

Research Assistant API is a FastAPI service for discovering and organising scholarly research data derived from OpenAlex.

The current MVP focuses on semantic discovery, metadata analytics, and research organisation workflows for the Leeds article subset.

## Current Status

The repository currently contains the raw Leeds articles CSV, the application foundation, and the first discovery API endpoints. The implemented batches currently cover:

- FastAPI service setup
- database foundation and Alembic migrations
- initial relational schema
- CSV ingestion for papers, topics, authors, institutions, and optional citation edges
- discovery endpoints for papers, authors, and topics
- pgvector-backed paper embedding support
- embedding generation pipeline using sentence-transformers
- analytics endpoints for top papers, topic distribution, publication trends, and co-authorship graph edges
- JWT-based authentication endpoints
- protected project CRUD endpoints
- protected reading list endpoints
- authenticated annotation endpoint
- similar papers endpoint
- project recommendation endpoint
- container deployment files for the API runtime
- smoke and endpoint tests

## Local Development

1. Copy `.env.example` to `.env`.
2. Start PostgreSQL with `docker compose up -d db`.
3. Create a virtual environment with `python -m venv .venv`.
4. Activate it with `.\.venv\Scripts\Activate.ps1`.
5. Install dependencies with `python -m pip install -r requirements-dev.txt`.
6. Run the API with `uvicorn research_assistant_api.main:app --reload`.

The default database configuration uses PostgreSQL with the `pgvector` image so vector support can be added later without replacing the local database container. The container is published on `localhost:5433` to avoid clashing with an existing PostgreSQL service on the default `5432` port.

The repository now includes:

- `requirements.txt` for pinned runtime dependencies
- `requirements-dev.txt` for local development tooling and tests
- `pyproject.toml` as the main package metadata source

The local `.venv` is a development convenience only. It is ignored by git and should not be committed.

## Testing

Run the smoke test suite with:

```bash
.\.venv\Scripts\python.exe -m pytest
```

The current tests cover:

- application startup
- health endpoint response
- SQLAlchemy session connectivity
- Alembic migration wiring against SQLite
- CSV ingestion for papers, topics, authors, institutions, and optional citation edges
- discovery API read endpoints for papers, authors, and topics
- embedding generation pipeline and similarity ranking
- analytics API read endpoints
- authentication endpoints and bearer-token access control
- protected project CRUD workflows
- protected reading list workflows
- authenticated annotation creation
- project recommendation ranking and access control

## Continuous Integration

GitHub Actions is configured in `.github/workflows/ci.yml`.

The workflow currently runs:

- Ruff lint checks on `src` and `tests`
- the Python smoke test suite on every push and pull request
- an Alembic migration check against PostgreSQL using a `pgvector` service container

## Virtualenv And Docker

The local `.venv` is for development on your machine. Docker does not use your host virtual environment.

In the current repo:

- `docker compose` is only used to run PostgreSQL locally
- the API itself runs from your local Python environment

If we add an application Dockerfile later, the container will install dependencies from `requirements.txt` or `pyproject.toml` inside the image. Your local `.venv` will not be copied into or reused by the container.

## Container Deployment

The repository now includes a `Dockerfile`, `.dockerignore`, and an optional `api` service in `docker-compose.yml`.

To run the API container locally alongside PostgreSQL:

```bash
docker compose --profile app up -d --build
```

The API container:

- waits for the PostgreSQL service to become healthy
- runs `alembic upgrade head` on startup
- serves the FastAPI app on port `8000`

Useful commands:

- `docker compose --profile app logs api --tail 100`
- `docker compose --profile app up -d db`
- `docker compose --profile app config`

The runtime image is intended for serving the API and using already stored embeddings. Embedding generation is still best run as an explicit job from the local development environment or a separate worker environment with the semantic dependencies available.

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

The importer now skips malformed source rows that are missing required paper fields such as `id` or `display_name`, and reports that skipped-row count in the CLI summary instead of aborting the whole import.

OpenAlex author IDs are treated as the authoritative author key during ingestion. ORCID values are stored as optional metadata, but they are not enforced as globally unique because the Leeds export contains repeated ORCIDs across different OpenAlex author records.

Paper titles and abstracts are stored without importer-side truncation so the full OpenAlex text can be retained even when individual rows exceed conservative `VARCHAR` lengths.

The same principle applies to DOI metadata: DOIs are retained when present, but they are not enforced as globally unique because the Leeds export contains repeated DOI values across different OpenAlex work IDs.

## Embeddings

Paper embeddings are generated from:

- `title + abstract`

If a paper has no abstract, the pipeline falls back to the title alone.

Generate embeddings with:

```bash
research-assistant-embed --limit 100
```

Useful options:

- `research-assistant-embed --paper-id https://openalex.org/W123`
- `research-assistant-embed --limit 100 --force`

Implementation notes:

- the CLI prints running progress as `Embedded X/Y papers` while each batch completes
- the final JSON summary is still written to standard output for scripting
- PostgreSQL stores embeddings in a `pgvector` column on `papers.embedding`
- similarity queries use cosine distance in Postgres
- SQLite tests store embeddings as JSON and rank with a Python cosine fallback
- the default model is `sentence-transformers/all-MiniLM-L6-v2`

## Dataset Limitation

The Leeds dataset currently loaded into the project contains aggregate citation counts such as `cited_by_count`, but not explicit work-to-work citation edges.

That means the current system can support:

- paper search and metadata lookup
- topic, author, and institution analytics
- popularity and influence ranking using `cited_by_count`
- a real co-authorship graph derived from paper authorship lists
- semantic similarity using stored embeddings
- user workflows such as projects, reading lists, and notes

It does not currently support true citation-graph operations such as:

- citation neighbourhood traversal
- shortest citation path discovery
- bridge-paper discovery through citation edges

Those graph features remain possible in the architecture, but only after ingesting a second source that contains explicit citation edge pairs.

For the report and presentation, the honest framing is:

- citation counts are used for influence-style analytics, not citation traversal
- the implemented graph feature is co-authorship, because that relationship exists directly in the ingested data
- the implemented recommendation feature uses embeddings plus reading-list context, not citation proximity
- citation-graph traversal is a planned extension that depends on a supplementary citation-edge source

## Current Scope

- paper discovery and metadata lookup
- corpus analytics and influence metrics based on `cited_by_count`
- co-authorship graph analytics
- JWT authentication
- project CRUD workflows
- reading list and annotation workflows
- semantic similarity via stored embeddings
- project recommendations via reading-list embedding context

## Implemented Authentication Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

Authentication uses bearer tokens signed with the JWT settings defined in `.env.example`.

## Implemented Project Endpoints

- `POST /projects`
- `GET /projects`
- `GET /projects/{id}`
- `PATCH /projects/{id}`
- `DELETE /projects/{id}`
- `GET /projects/{id}/recommendations`

Project routes are scoped to the authenticated user, so users can only see and modify their own projects.

Project recommendations are built from the embeddings of papers already saved in the project's reading list. Candidate papers already present in the reading list are excluded, and ranking is based on semantic similarity to the project embedding centroid.

## Implemented Reading List Endpoints

- `POST /projects/{id}/reading-list`
- `GET /projects/{id}/reading-list`
- `PATCH /reading-list-items/{id}`
- `DELETE /reading-list-items/{id}`

Reading list items are scoped through the owning project, so users can only manage items in their own projects.

## Implemented Annotation Endpoint

- `POST /papers/{id}/annotations`

Annotations currently support authenticated creation. Listing and editing annotations can be added later if needed.

## Implemented Discovery Endpoints

- `GET /papers/search`
- `GET /papers/{id}`
- `GET /papers/{id}/similar`
- `GET /authors/{id}`
- `GET /authors/{id}/papers`
- `GET /topics`
- `GET /topics/{id}/papers`

## Implemented Analytics Endpoints

- `GET /analytics/top-papers`
- `GET /analytics/topics`
- `GET /analytics/trends`
- `GET /analytics/collaborations`

The collaboration endpoint exposes co-authorship edges between authors. This is a real graph derived from the authorship data in the Leeds CSV. It is not a citation graph. Institution-level collaboration graphs would need richer affiliation-per-authorship modelling.

## Future Extension

- citation graph exploration via supplementary citation-edge ingestion
- shortest citation path and neighbourhood endpoints once citation edges are available
- hybrid recommendation scoring that includes citation proximity once citation edges are available
