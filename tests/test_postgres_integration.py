from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, text

from research_assistant_api.db.session import get_session_factory
from research_assistant_api.embeddings.service import EMBEDDING_DIMENSIONS
from research_assistant_api.models import Paper
from research_assistant_api.repositories.similarity_repository import SimilarityRepository

pytestmark = pytest.mark.skipif(
    os.getenv("RESEARCH_API_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are only enabled explicitly",
)


def _database_url() -> str:
    database_url = os.getenv("RESEARCH_API_DATABASE_URL")
    if not database_url:
        raise AssertionError("RESEARCH_API_DATABASE_URL must be set for PostgreSQL tests")
    return database_url


def _embedding(*leading_values: float) -> list[float]:
    padding = max(EMBEDDING_DIMENSIONS - len(leading_values), 0)
    return [*leading_values, *([0.0] * padding)]


def test_postgres_schema_contains_lookup_and_vector_indexes() -> None:
    session_factory = get_session_factory(_database_url())

    with session_factory() as session:
        rows = session.execute(
            text(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename IN ('citations', 'papers')
                """
            )
        ).all()

    indexes = {row[0]: row[1] for row in rows}
    assert "ix_citations_citing_paper_id" in indexes
    assert "ix_citations_cited_paper_id" in indexes
    assert "ix_papers_embedding_ivfflat" in indexes
    assert "ivfflat" in indexes["ix_papers_embedding_ivfflat"]
    assert "vector_cosine_ops" in indexes["ix_papers_embedding_ivfflat"]


def test_postgres_similarity_repository_ranks_vectors_with_pgvector() -> None:
    session_factory = get_session_factory(_database_url())
    suffix = uuid4().hex
    paper_ids = {
        "target": f"https://openalex.org/W-postgres-target-{suffix}",
        "close": f"https://openalex.org/W-postgres-close-{suffix}",
        "far": f"https://openalex.org/W-postgres-far-{suffix}",
    }

    with session_factory() as session:
        session.add_all(
            [
                Paper(
                    id=paper_ids["target"],
                    title="Target Paper",
                    abstract="Reference embedding",
                    publication_year=2024,
                    citation_count=10,
                    embedding=_embedding(1.0, 0.0, 0.0),
                ),
                Paper(
                    id=paper_ids["close"],
                    title="Close Match",
                    abstract="Nearest vector",
                    publication_year=2024,
                    citation_count=8,
                    embedding=_embedding(0.999, 0.001, 0.0),
                ),
                Paper(
                    id=paper_ids["far"],
                    title="Second Match",
                    abstract="Second-closest vector",
                    publication_year=2023,
                    citation_count=5,
                    embedding=_embedding(0.998, 0.002, 0.0),
                ),
            ]
        )
        session.commit()

        try:
            target_paper = session.scalar(
                select(Paper).where(Paper.id == paper_ids["target"])
            )
            assert target_paper is not None

            results = SimilarityRepository(session).list_similar(
                target_paper,
                limit=2,
                offset=0,
            )

            assert [record.paper.id for record in results] == [
                paper_ids["close"],
                paper_ids["far"],
            ]
            assert results[0].similarity_score > results[1].similarity_score
        finally:
            session.execute(
                delete(Paper).where(Paper.id.in_(paper_ids.values()))
            )
            session.commit()
