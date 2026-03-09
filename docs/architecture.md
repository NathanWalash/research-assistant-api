# Architecture

The codebase follows a layered structure:

1. `api/`
   HTTP routes, dependency injection, and HTTP error mapping.
2. `services/`
   Business logic and orchestration across repositories.
3. `repositories/`
   SQLAlchemy query logic and persistence operations.
4. `models/`
   ORM models and relationships.
5. `schemas/`
   Pydantic request and response models.
6. `db/`
   Engine, session, and declarative metadata helpers.

## Core Data Flows

- Discovery flow:
  route -> service -> repository -> `papers/authors/topics`
- Research workflow flow:
  route -> service -> repository -> `projects/reading_list_items/annotations`
- Similarity flow:
  route -> service -> similarity repository -> pgvector cosine query
- Citation flow:
  route -> service -> citation repository -> Leeds citation subgraph

## Storage Strategy

- PostgreSQL stores relational metadata and workflow state.
- `pgvector` stores paper embeddings on `papers.embedding`.
- SQLite is used only for lightweight local tests with a JSON embedding fallback.

## Boundary Decisions

- Citation traversal is limited to a Leeds-only citation subgraph.
- Recommendation scoring is explicit and configurable instead of hiding the ranking formula.
- Long-running enrichment tasks are handled via CLI commands rather than synchronous API endpoints.
