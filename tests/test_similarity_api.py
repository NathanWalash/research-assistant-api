from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.main import create_app
from research_assistant_api.models import Paper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _seed_similarity_dataset(database_url: str) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds.csv",
        citation_csv_path=None,
        batch_size=10,
    )

    with session_factory() as session:
        CsvIngestionService(session).ingest(config)
        papers = {
            paper.id: paper
            for paper in session.scalars(select(Paper)).all()
        }
        papers["https://openalex.org/W1"].embedding = [1.0, 0.0, 0.0]
        papers["https://openalex.org/W2"].embedding = [0.9, 0.1, 0.0]
        session.add(
            Paper(
                id="https://openalex.org/W3",
                title="Paper Three",
                abstract="Synthetic paper for similarity tests",
                publication_year=2022,
                citation_count=7,
                journal="Journal Three",
                embedding=[0.2, 0.98, 0.0],
            )
        )
        session.add(
            Paper(
                id="https://openalex.org/W4",
                title="Paper Four",
                abstract="No embedding yet",
                publication_year=2021,
                citation_count=1,
                journal="Journal Four",
            )
        )
        session.commit()


@pytest.fixture
def client(sqlite_database_url: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    _seed_similarity_dataset(sqlite_database_url)
    return TestClient(create_app())


def test_similar_papers_endpoint_returns_ranked_results(client: TestClient) -> None:
    response = client.get("/papers/https://openalex.org/W1/similar")

    assert response.status_code == 200
    body = response.json()
    assert [paper["id"] for paper in body] == [
        "https://openalex.org/W2",
        "https://openalex.org/W3",
    ]
    assert body[0]["similarity_score"] > body[1]["similarity_score"]


def test_similar_papers_endpoint_rejects_unembedded_target(client: TestClient) -> None:
    response = client.get("/papers/https://openalex.org/W4/similar")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "paper 'https://openalex.org/W4' does not have an embedding yet"
    )


def test_similar_papers_endpoint_returns_not_found_for_missing_paper(
    client: TestClient,
) -> None:
    response = client.get("/papers/https://openalex.org/W999/similar")

    assert response.status_code == 404
    assert response.json()["detail"] == "paper 'https://openalex.org/W999' was not found"
