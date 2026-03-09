# Configuration

Environment variables use the `RESEARCH_API_` prefix.

| Variable | Purpose | Default |
| --- | --- | --- |
| `RESEARCH_API_APP_NAME` | OpenAPI/service display name | `Research Assistant API` |
| `RESEARCH_API_APP_VERSION` | API version string | `0.1.0` |
| `RESEARCH_API_ENVIRONMENT` | Runtime mode: `development`, `test`, `production` | `development` |
| `RESEARCH_API_DEBUG` | FastAPI debug mode | `false` |
| `RESEARCH_API_API_PREFIX` | Optional API route prefix | empty |
| `RESEARCH_API_DATABASE_URL` | SQLAlchemy database URL | local Postgres on `localhost:5433` |
| `RESEARCH_API_JWT_SECRET_KEY` | HMAC secret used for bearer tokens | development placeholder |
| `RESEARCH_API_JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `RESEARCH_API_JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime in minutes | `60` |
| `RESEARCH_API_EMBEDDING_MODEL_NAME` | Sentence-transformer model for embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| `RESEARCH_API_EMBEDDING_BATCH_SIZE` | Batch size for embedding generation | `32` |
| `RESEARCH_API_EMBEDDING_DIMENSIONS` | Expected vector dimensions | `384` |
| `RESEARCH_API_CITATION_EDGES_CSV_PATH` | Optional citation-edge CSV for ingestion | `data/derived/leeds_citation_edges.csv` |

## Production Notes

- Production rejects the placeholder JWT secret.
- Production also requires a JWT secret with at least `32` characters.
- The local Docker Compose file still uses development defaults and is not production deployment config.
