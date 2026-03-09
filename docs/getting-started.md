# Getting Started

## Local API Workflow

1. Copy `.env.example` to `.env`.
2. Start PostgreSQL:

```bash
docker compose up -d db
```

3. Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Install the development environment:

```bash
python -m pip install -e ".[dev]"
```

Pinned alternative:

```bash
python -m pip install -r requirements-dev.txt
```

5. Apply migrations:

```bash
.\.venv\Scripts\python.exe -m alembic upgrade head
```

6. Ingest the Leeds dataset:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.ingestion.cli
```

7. Generate embeddings:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.embeddings.cli
```

8. Run the API:

```bash
.\.venv\Scripts\python.exe -m uvicorn research_assistant_api.main:app --reload
```

The API will then be available on `http://127.0.0.1:8000`.

The interactive frontend will be available on `http://127.0.0.1:8000/app` with separate pages for:

- discovery
- projects
- analytics
- account
- login and registration

## Optional Citation Graph Enrichment

To fetch Leeds-to-Leeds citation edges from OpenAlex and resume automatically if interrupted:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.citation_graph.cli --rate-interval 0.2
```

Then re-import the generated edge CSV:

```bash
.\.venv\Scripts\python.exe -m research_assistant_api.ingestion.cli --citation-csv-path data/derived/leeds_citation_edges.csv
```

## Local Verification

Run the main local checks with:

```bash
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest
```
