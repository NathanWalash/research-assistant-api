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
