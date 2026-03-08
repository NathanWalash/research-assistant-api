from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _seed_discovery_dataset(database_url: str) -> None:
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
    _seed_discovery_dataset(sqlite_database_url)
    return TestClient(create_app())


def test_paper_search_filters_by_query_and_year(client: TestClient) -> None:
    response = client.get(
        "/papers/search",
        params={"query": "Paper", "year": 2024},
    )

    assert response.status_code == 200
    body = response.json()
    assert [paper["id"] for paper in body] == ["https://openalex.org/W1"]
    assert body[0]["topic"]["id"] == "topic:computer-vision"


def test_paper_search_filters_by_topic_and_minimum_citations(
    client: TestClient,
) -> None:
    response = client.get(
        "/papers/search",
        params={"topic": "Artificial Intelligence", "citation_count": 3},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "https://openalex.org/W2",
            "title": "Paper Two",
            "publication_year": 2023,
            "publication_date": "2023-09-01",
            "citation_count": 3,
            "doi": None,
            "journal": "Journal Two",
            "language": "en",
            "work_type": "article",
            "topic": {
                "id": "topic:artificial-intelligence",
                "name": "Artificial Intelligence",
                "field": None,
            },
        }
    ]


def test_paper_detail_returns_metadata_and_sorted_authors(client: TestClient) -> None:
    response = client.get("/papers/https://openalex.org/W1")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "https://openalex.org/W1"
    assert body["abstract"] == "Sample abstract one"
    assert [author["name"] for author in body["authors"]] == [
        "Alice Smith",
        "Bob Jones",
    ]
    assert body["authors"][0]["institution"]["id"] == "https://openalex.org/I1"
    assert body["authors"][0]["author_position"] == 1


def test_author_endpoints_return_author_profile_and_papers(client: TestClient) -> None:
    author_response = client.get("/authors/https://openalex.org/A1")
    papers_response = client.get("/authors/https://openalex.org/A1/papers")

    assert author_response.status_code == 200
    assert author_response.json() == {
        "id": "https://openalex.org/A1",
        "name": "Alice Smith",
        "orcid": "https://orcid.org/0000-0000-0000-0001",
        "institution": {
            "id": "https://openalex.org/I1",
            "name": "University of Leeds",
            "country": "GB",
        },
        "paper_count": 2,
    }

    assert papers_response.status_code == 200
    assert [paper["id"] for paper in papers_response.json()] == [
        "https://openalex.org/W1",
        "https://openalex.org/W2",
    ]


def test_topic_endpoints_return_topics_and_topic_papers(client: TestClient) -> None:
    topics_response = client.get("/topics")
    topic_papers_response = client.get("/topics/topic:computer-vision/papers")

    assert topics_response.status_code == 200
    assert topics_response.json() == [
        {
            "id": "topic:artificial-intelligence",
            "name": "Artificial Intelligence",
            "field": None,
            "paper_count": 1,
        },
        {
            "id": "topic:computer-vision",
            "name": "Computer Vision",
            "field": None,
            "paper_count": 1,
        },
    ]

    assert topic_papers_response.status_code == 200
    assert [paper["id"] for paper in topic_papers_response.json()] == [
        "https://openalex.org/W1"
    ]


def test_discovery_endpoints_return_not_found_for_missing_resources(
    client: TestClient,
) -> None:
    missing_paper = client.get("/papers/https://openalex.org/W999")
    missing_author = client.get("/authors/https://openalex.org/A999")
    missing_topic = client.get("/topics/topic:missing/papers")

    assert missing_paper.status_code == 404
    assert missing_author.status_code == 404
    assert missing_topic.status_code == 404
    assert (
        missing_paper.json()["detail"]
        == "paper 'https://openalex.org/W999' was not found"
    )
