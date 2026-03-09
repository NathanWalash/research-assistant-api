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


def _create_project(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/projects",
        json={"title": "Literature Review", "description": "Project notes"},
        headers=headers,
    )
    return response.json()["id"]


def test_add_and_list_reading_list_items(client: TestClient) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)

    add_response = client.post(
        f"/projects/{project_id}/reading-list",
        json={
            "paper_id": "https://openalex.org/W1",
            "priority": "high",
            "notes": "Start with this paper",
        },
        headers=headers,
    )
    list_response = client.get(f"/projects/{project_id}/reading-list", headers=headers)

    assert add_response.status_code == 201
    assert add_response.json()["paper"]["title"] == "Paper One"
    assert add_response.json()["priority"] == "high"
    assert list_response.status_code == 200
    assert [item["paper_id"] for item in list_response.json()] == [
        "https://openalex.org/W1"
    ]


def test_reading_list_update_and_delete_workflow(client: TestClient) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)

    add_response = client.post(
        f"/projects/{project_id}/reading-list",
        json={"paper_id": "https://openalex.org/W1"},
        headers=headers,
    )
    item_id = add_response.json()["id"]

    update_response = client.patch(
        f"/reading-list-items/{item_id}",
        json={"priority": "low", "notes": "Read later"},
        headers=headers,
    )
    delete_response = client.delete(f"/reading-list-items/{item_id}", headers=headers)
    list_response = client.get(f"/projects/{project_id}/reading-list", headers=headers)

    assert update_response.status_code == 200
    assert update_response.json()["priority"] == "low"
    assert update_response.json()["notes"] == "Read later"
    assert delete_response.status_code == 204
    assert list_response.json() == []


def test_reading_list_rejects_duplicate_paper_entries(client: TestClient) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)

    first_response = client.post(
        f"/projects/{project_id}/reading-list",
        json={"paper_id": "https://openalex.org/W1"},
        headers=headers,
    )
    second_response = client.post(
        f"/projects/{project_id}/reading-list",
        json={"paper_id": "https://openalex.org/W1"},
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "paper 'https://openalex.org/W1' is already in the reading list"
    )


def test_reading_list_rejects_missing_paper(client: TestClient) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)

    response = client.post(
        f"/projects/{project_id}/reading-list",
        json={"paper_id": "https://openalex.org/W999"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "paper 'https://openalex.org/W999' was not found"


def test_reading_list_routes_enforce_ownership(client: TestClient) -> None:
    owner_headers = _register_user(client, "owner@example.com")
    other_headers = _register_user(client, "other@example.com")
    project_id = _create_project(client, owner_headers)
    add_response = client.post(
        f"/projects/{project_id}/reading-list",
        json={"paper_id": "https://openalex.org/W1"},
        headers=owner_headers,
    )
    item_id = add_response.json()["id"]

    list_response = client.get(f"/projects/{project_id}/reading-list", headers=other_headers)
    update_response = client.patch(
        f"/reading-list-items/{item_id}",
        json={"priority": "high"},
        headers=other_headers,
    )
    delete_response = client.delete(f"/reading-list-items/{item_id}", headers=other_headers)

    assert list_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
