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

The default database configuration uses PostgreSQL with the `pgvector` image so vector support can be added later without replacing the local database container.

## Planned Capabilities

- paper discovery and metadata lookup
- citation graph exploration
- semantic similarity and recommendations
- project, reading list, and annotation workflows
- research analytics endpoints
