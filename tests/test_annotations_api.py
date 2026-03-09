from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _seed_dataset(database_url: str) -> None:
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
    monkeypatch.setenv("RESEARCH_API_JWT_SECRET_KEY", "test-secret-key")
    _seed_dataset(sqlite_database_url)
    return TestClient(create_app())


def _register_user(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password"},
    )
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_create_annotation_returns_saved_annotation(client: TestClient) -> None:
    headers = _register_user(client, "annotator@example.com")

    response = client.post(
        "/papers/https://openalex.org/W1/annotations",
        json={"text": " Important note "},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["paper_id"] == "https://openalex.org/W1"
    assert body["text"] == "Important note"


def test_create_annotation_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/papers/https://openalex.org/W1/annotations",
        json={"text": "Important note"},
    )

    assert response.status_code == 401


def test_create_annotation_rejects_missing_paper(client: TestClient) -> None:
    headers = _register_user(client, "annotator@example.com")

    response = client.post(
        "/papers/https://openalex.org/W999/annotations",
        json={"text": "Important note"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "paper 'https://openalex.org/W999' was not found"
