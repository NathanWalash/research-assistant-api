from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _seed_analytics_dataset(database_url: str) -> None:
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


@pytest.fixture
def client(sqlite_database_url: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    _seed_analytics_dataset(sqlite_database_url)
    return TestClient(create_app())


def test_top_papers_endpoint_returns_ranked_papers(client: TestClient) -> None:
    response = client.get("/analytics/top-papers")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "https://openalex.org/W1",
            "title": "Paper One",
            "publication_year": 2024,
            "citation_count": 12,
            "journal": "Journal One",
            "topic": {
                "id": "topic:computer-vision",
                "name": "Computer Vision",
                "field": None,
            },
        },
        {
            "id": "https://openalex.org/W2",
            "title": "Paper Two",
            "publication_year": 2023,
            "citation_count": 3,
            "journal": "Journal Two",
            "topic": {
                "id": "topic:artificial-intelligence",
                "name": "Artificial Intelligence",
                "field": None,
            },
        },
    ]


def test_top_papers_endpoint_supports_topic_filter(client: TestClient) -> None:
    response = client.get(
        "/analytics/top-papers",
        params={"topic": "topic:artificial-intelligence"},
    )

    assert response.status_code == 200
    assert [paper["id"] for paper in response.json()] == ["https://openalex.org/W2"]


def test_topic_distribution_endpoint_returns_topic_metrics(client: TestClient) -> None:
    response = client.get("/analytics/topics")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "topic:computer-vision",
            "name": "Computer Vision",
            "field": None,
            "paper_count": 1,
            "total_citation_count": 12,
            "average_citation_count": 12.0,
        },
        {
            "id": "topic:artificial-intelligence",
            "name": "Artificial Intelligence",
            "field": None,
            "paper_count": 1,
            "total_citation_count": 3,
            "average_citation_count": 3.0,
        },
    ]


def test_publication_trends_endpoint_supports_year_filters(client: TestClient) -> None:
    response = client.get("/analytics/trends", params={"start_year": 2024})

    assert response.status_code == 200
    assert response.json() == [
        {
            "publication_year": 2024,
            "paper_count": 1,
            "total_citation_count": 12,
            "average_citation_count": 12.0,
        }
    ]


def test_collaborations_endpoint_returns_coauthor_pairs(client: TestClient) -> None:
    response = client.get("/analytics/collaborations")

    assert response.status_code == 200
    assert response.json() == [
        {
            "author_a_id": "https://openalex.org/A1",
            "author_a_name": "Alice Smith",
            "author_b_id": "https://openalex.org/A2",
            "author_b_name": "Bob Jones",
            "shared_paper_count": 1,
        },
        {
            "author_a_id": "https://openalex.org/A1",
            "author_a_name": "Alice Smith",
            "author_b_id": "https://openalex.org/A3",
            "author_b_name": "Cara Patel",
            "shared_paper_count": 1,
        },
    ]
