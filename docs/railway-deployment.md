# Railway Deployment

This repo is set up to deploy on Railway using the root `Dockerfile`.

## What Is Already Prepared

- `Dockerfile` builds the API image
- `docker/entrypoint.sh` runs `alembic upgrade head` before starting the app
- `railway.toml` sets Dockerfile deploy mode plus `/health` as the deployment healthcheck
- the app listens on Railway's injected `PORT` variable
- config now accepts Railway-style `postgres://` and `postgresql://` database URLs and normalizes them to the SQLAlchemy `postgresql+psycopg://` form

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

## First Deployment

Once those variables are saved and deployed:

1. Railway will build the Docker image from the repo root.
2. Railway will start the container.
3. The container entrypoint will run `alembic upgrade head`.
4. Railway will wait for `GET /health` to return `200`.

At this point the API service is live, but the database will still be empty.

## Loading Data Into Railway Postgres

The easiest path is to load the Railway Postgres database from your local machine.

### Option 1. Ingest directly into Railway Postgres

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

### Option 2. Restore from an existing dump

If you already have a fully populated local Postgres instance, you can also export and restore that data into Railway Postgres instead of re-running ingestion and embeddings.

## Verification Checklist

After deployment:

1. open `/health`
2. open `/openapi.json`
3. register a user
4. query `/papers/search`
5. test `/papers/{id}/similar`
6. test `/projects/{id}/recommendations` after creating a project and adding reading-list papers

## Limits And Practical Notes

- Railway trial resources are limited, so full embedding generation may take time and consume trial credit.
- The deployed app image is only intended to serve the API. Heavy ingestion and embedding jobs are better run from your local machine against the Railway database.
- Railway healthchecks only validate startup readiness, not ongoing application health after deployment.
