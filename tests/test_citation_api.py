from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _seed_citation_dataset(database_url: str) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds_graph.csv",
        citation_csv_path=FIXTURES_DIR / "sample_citation_graph_edges.csv",
        batch_size=10,
    )

    with session_factory() as session:
        CsvIngestionService(session).ingest(config)


@pytest.fixture
def client(sqlite_database_url: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    _seed_citation_dataset(sqlite_database_url)
    return TestClient(create_app())


def test_citation_neighborhood_returns_cited_and_citing_papers(
    client: TestClient,
) -> None:
    response = client.get("/papers/https://openalex.org/W2/citations")

    assert response.status_code == 200
    assert response.json() == {
        "paper_id": "https://openalex.org/W2",
        "cited_papers": [
            {
                "id": "https://openalex.org/W1",
                "title": "Paper One",
                "publication_year": 2024,
                "publication_date": "2024-01-15",
                "citation_count": 12,
                "doi": "https://doi.org/10.1234/one",
                "journal": "Journal One",
                "language": "en",
                "work_type": "article",
                "topic": {
                    "id": "topic:computer-vision",
                    "name": "Computer Vision",
                    "field": None,
                },
            }
        ],
        "citing_papers": [
            {
                "id": "https://openalex.org/W3",
                "title": "Paper Three",
                "publication_year": 2022,
                "publication_date": "2022-06-11",
                "citation_count": 6,
                "doi": "https://doi.org/10.1234/three",
                "journal": "Journal Three",
                "language": "en",
                "work_type": "article",
                "topic": {
                    "id": "topic:knowledge-graphs",
                    "name": "Knowledge Graphs",
                    "field": None,
                },
            },
            {
                "id": "https://openalex.org/W4",
                "title": "Paper Four",
                "publication_year": 2021,
                "publication_date": "2021-02-20",
                "citation_count": 1,
                "doi": "https://doi.org/10.1234/four",
                "journal": "Journal Four",
                "language": "en",
                "work_type": "article",
                "topic": {
                    "id": "topic:machine-learning",
                    "name": "Machine Learning",
                    "field": None,
                },
            },
        ],
    }


def test_citation_path_returns_directed_shortest_path(client: TestClient) -> None:
    response = client.get(
        "/papers/https://openalex.org/W3/path/https://openalex.org/W1"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_paper_id"] == "https://openalex.org/W3"
    assert body["target_paper_id"] == "https://openalex.org/W1"
    assert body["path_length"] == 2
    assert [paper["id"] for paper in body["path"]] == [
        "https://openalex.org/W3",
        "https://openalex.org/W2",
        "https://openalex.org/W1",
    ]


def test_citation_path_returns_not_found_when_no_directed_path_exists(
    client: TestClient,
) -> None:
    response = client.get(
        "/papers/https://openalex.org/W1/path/https://openalex.org/W4"
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "No citation path found from 'https://openalex.org/W1' to "
        "'https://openalex.org/W4' within depth 6"
    )


def test_citation_endpoints_return_not_found_for_missing_papers(
    client: TestClient,
) -> None:
    neighborhood_response = client.get("/papers/https://openalex.org/W999/citations")
    path_response = client.get(
        "/papers/https://openalex.org/W1/path/https://openalex.org/W999"
    )

    assert neighborhood_response.status_code == 404
    assert path_response.status_code == 404
