# Troubleshooting

## PostgreSQL Port Conflict

The local database container uses `localhost:5433` instead of `5432` to avoid clashing with an existing local PostgreSQL instance.

## Embeddings Only Process A Few Papers

The embedding CLI only works on papers already stored in the database. If it reports `5/5`, you only ingested `5` papers.

Fix:

1. run the full ingestion command
2. check the `papers` table count
3. rerun the embedding CLI

## Citation Export Feels Slow

The export is network-bound and writes resumable state after each batch. This is normal. Avoid opening the large JSONL audit file in the editor while the export is still running.

## Citation Paths Missing

Citation paths are only complete inside the Leeds citation subgraph. Paths that need non-Leeds intermediary papers will not exist in the local graph.

## Production Startup Fails On JWT Secret

Production mode rejects:

- the placeholder development secret
- JWT secrets shorter than `32` characters

Set `RESEARCH_API_JWT_SECRET_KEY` to a strong production value before starting the app.
