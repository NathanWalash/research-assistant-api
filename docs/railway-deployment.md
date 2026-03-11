# Railway Deployment

This repo is set up to deploy on Railway using the root `Dockerfile`.

## What Is Already Prepared

- `Dockerfile` builds the API image
- `docker/entrypoint.sh` runs `alembic upgrade head` before starting the app
- `railway.toml` sets Dockerfile deploy mode plus `/health` as the deployment healthcheck
- the app listens on Railway's injected `PORT` variable
- config now accepts Railway-style `postgres://` and `postgresql://` database URLs and normalizes them to the SQLAlchemy `postgresql+psycopg://` form
- static frontend is served by the same app under `/app`
- MCP HTTP mount is optional via `RESEARCH_API_MCP_ENABLED=true`

## Railway Project Setup

1. Create a new Railway project.
2. Add a `PostgreSQL` service.
3. Add a service from your GitHub repo for this API.
4. In the API service, ensure Railway uses the root `Dockerfile`.
5. Generate a public domain for the API service.

## Required API Variables

Set these in the API service's Variables tab:

- `RESEARCH_API_ENVIRONMENT=production`
- `RESEARCH_API_JWT_SECRET_KEY=<long-random-secret-at-least-32-characters>`
- `RESEARCH_API_DATABASE_URL=${{Postgres.DATABASE_URL}}`

Important note:

- If your database service is not literally named `Postgres`, replace `Postgres` with the actual Railway service name.
- Railway reference variables use the `${{SERVICE_NAME.VAR}}` form.

## Recommended Optional Variables

- `RESEARCH_API_APP_NAME=Research Assistant API`
- `RESEARCH_API_APP_VERSION=0.1.0`
- `RESEARCH_API_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `RESEARCH_API_MCP_ENABLED=false`
- `RESEARCH_API_MCP_MOUNT_PATH=/mcp`

## First Deployment

Once those variables are saved and deployed:

1. Railway will build the Docker image from the repo root.
2. Railway will start the container.
3. The container entrypoint will run `alembic upgrade head`.
4. Railway will wait for `GET /health` to return `200`.

At this point the API service is live, but the database will still be empty.

## Loading Data Into Railway Postgres

There are two valid paths. The recommended one is snapshot/restore because it avoids rerunning heavy ingestion/embedding jobs in a constrained hosted shell.

### Recommended Path: Snapshot/Restore (No Pipeline Re-run)

Use this when your local database is already populated with:

- metadata ingestion
- citation-edge ingestion
- generated embeddings

#### A) Build data locally once

```bash
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m research_assistant_api.ingestion.cli --citation-csv-path data/derived/leeds_citation_edges.csv
.\.venv\Scripts\python.exe -m research_assistant_api.embeddings.cli
```

#### B) Export data-only snapshot from local Postgres

```bash
pg_dump --data-only --no-owner --no-privileges --format=custom --file artifacts/research_assistant_data.dump "postgresql://research_user:research_password@localhost:5433/research_assistant"
```

#### C) Deploy app on Railway (schema migrations on startup)

The container entrypoint applies migrations automatically.

#### D) Restore snapshot into Railway Postgres

```bash
pg_restore --data-only --no-owner --no-privileges --dbname "$RAILWAY_DATABASE_URL" artifacts/research_assistant_data.dump
```

#### E) Verify seed success

- `GET /health`
- `GET /papers/search`
- `GET /papers/{id}/similar`
- `GET /papers/{id}/citations`
- `/app` frontend loads and can search papers

### Alternative Path: Direct Local Jobs Against Railway DB

From your local machine:

1. copy the external connection string from the Railway PostgreSQL service
2. temporarily set `RESEARCH_API_DATABASE_URL` locally to that Railway connection string
3. run:

```bash
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m research_assistant_api.ingestion.cli
.\.venv\Scripts\python.exe -m research_assistant_api.embeddings.cli
```

4. if you want citation traversal on Railway as well, also run:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.ingestion.cli --citation-csv-path data/derived/leeds_citation_edges.csv
```

## Verification Checklist

After deployment:

1. open `/health`
2. open `/app` and confirm the frontend loads
3. open `/openapi.json`
4. register a user from `/app/register` or the API directly
5. query `/papers/search`
6. test `/papers/{id}/similar`
7. test `/projects/{id}/recommendations` after creating a project and adding reading-list papers

## Limits And Practical Notes

- Railway trial resources are limited, so full embedding generation may take time and consume trial credit.
- The deployed app image is intended to serve the API. Heavy ingestion and embedding jobs should run locally or via one-off job containers.
- Railway healthchecks only validate startup readiness, not ongoing application health after deployment.
- The same Railway service also serves the static frontend from `/app`, so you do not need a separate frontend host for the coursework demo.
- For repeatable deploys, keep a versioned snapshot artifact strategy for dataset refreshes rather than ad-hoc shell commands on production databases.
