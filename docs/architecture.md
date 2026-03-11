# Architecture

## Layered Design

The codebase is organized into explicit layers:

1. `api/`
   FastAPI route handlers, dependency wiring, request validation, and HTTP error translation.
2. `services/`
   Business rules and orchestration logic independent from HTTP transport.
3. `repositories/`
   SQLAlchemy query and persistence operations.
4. `models/`
   ORM entities and relationships.
5. `schemas/`
   Pydantic request/response contracts.
6. `db/`
   engine/session factories, database URL normalization, and metadata setup.
7. `ingestion/`, `embeddings/`, `citation_graph/`, `mcp/`
   operational pipelines and MCP integration.

The boundaries are intentional:

- route handlers stay thin and focused on I/O and status-code semantics
- services remain unit-testable with repository dependencies
- repositories isolate SQL/dialect details away from API and business rules

## Runtime Request Flows

Discovery flow:

```text
HTTP request -> API route -> service -> repository -> PostgreSQL -> response schema
```

Similarity flow:

```text
HTTP request -> API route -> SimilarityService -> SimilarityRepository
-> pgvector cosine ordering (or SQLite fallback in tests) -> response
```

Citation traversal flow:

```text
HTTP request -> CitationGraphService -> CitationRepository
-> directed edge traversal over citations table -> neighborhood/path response
```

User workflow flow:

```text
HTTP request + JWT -> auth dependency -> Project/ReadingList/Annotation services
-> ownership-enforced repository operations -> response
```

## Data Structures

Relational core:

- `papers` (metadata + embedding vector)
- `authors`, `institutions`, `topics`
- `paper_authors` association table
- `citations` directed edge list (`citing_paper_id`, `cited_paper_id`)

User workflow:

- `users`
- `projects`
- `reading_list_items`
- `annotations`

Graph representation:

- citation graph is represented as a directed edge table, not a denormalized JSON graph blob
- this keeps inserts/querying composable and indexable with SQL

Vector representation:

- PostgreSQL: `pgvector` column on `papers.embedding`
- SQLite test path: JSON/text-backed vectors and Python cosine fallback for deterministic CI portability

## Algorithmic Notes And Complexity

### Paper Search

Parameters: free-text query, topic, year, citation threshold, limit/offset.

- complexity is query-shape dependent, typically `O(log N + K)` with indexes for selective filters and result size `K`
- count-free pagination avoids a separate full count query

### Similarity Ranking

Input: source paper embedding and candidate corpus.

- PostgreSQL path uses vector distance ordering; candidate ranking cost scales with candidate set size
- approximate complexity is `O(C)` distance evaluations for `C` candidates, with database planner/index strategy affecting practical latency

### Citation Neighborhood

Input: paper ID.

- direct neighbors are one-hop lookups on `citations`
- complexity `O(out_degree + in_degree)` plus metadata hydration cost

### Citation Path

Input: source ID, target ID, `max_depth`.

- service uses bounded BFS on directed edges
- worst-case bounded complexity `O(V + E)` within the explored subgraph up to depth limit

### Recommendation Scoring

Modes: `semantic`, `citation`, `hybrid`.

- semantic component aggregates similarity from project reading-list context
- citation component scores direct citation linkage to reading-list papers
- hybrid combines both with configurable weights

Practical complexity:

- approximately `O(C * K)` for `C` candidates and `K` context papers in the semantic component
- citation contribution is proportional to candidate linkage checks against context edges

## Pipeline Architecture

Pipelines are separate CLI units by design, not API startup work:

- ingestion pipeline (`ingestion.cli`)
- embedding pipeline (`embeddings.cli`)
- citation export pipeline (`citation_graph.cli`)

Benefits:

- deployment startup remains fast and deterministic
- heavy work can run offline or as one-off jobs
- failed long-running jobs can be resumed/retried independently

## Dialect And Environment Strategy

- production/deployment target: PostgreSQL + pgvector
- test default: SQLite for fast local/CI iteration
- Postgres-only behavior validated with dedicated integration tests and CI service containers

This split gives high confidence without forcing every local run to spin up full infrastructure.

## Explicit Boundary Decisions

- citation traversal is intentionally limited to the Leeds citation subgraph available in the local corpus
- recommendation scoring exposes mode/weight controls explicitly in API contract
- MCP tools are read-only and restricted to public/discovery-style operations; authenticated mutation routes are intentionally excluded
