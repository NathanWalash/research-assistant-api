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
    monkeypatch.setenv(
        "RESEARCH_API_JWT_SECRET_KEY",
        "test-secret-key-with-32-byte-minimum",
    )
    _seed_dataset(sqlite_database_url)
    return TestClient(create_app())


def _register_user(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/projects",
        json={"title": "Coverage Project", "description": "Test"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_openapi_inventory_matches_expected_api_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    actual_routes = {
        (method.upper(), path)
        for path, operations in payload["paths"].items()
        for method in operations
        if method in {"get", "post", "patch", "delete", "put"}
    }

    expected_routes = {
        ("GET", "/health"),
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        ("GET", "/auth/me"),
        ("GET", "/papers/search"),
        ("GET", "/papers/{paper_id}"),
        ("GET", "/papers/{paper_id}/similar"),
        ("GET", "/papers/{paper_id}/citations"),
        ("GET", "/papers/{paper_id}/path/{target_paper_id}"),
        ("POST", "/papers/{paper_id}/annotations"),
        ("GET", "/papers/{paper_id}/annotations"),
        ("GET", "/authors"),
        ("GET", "/authors/search"),
        ("GET", "/authors/{author_id}"),
        ("GET", "/authors/{author_id}/papers"),
        ("GET", "/topics"),
        ("GET", "/topics/{topic_id}/papers"),
        ("GET", "/analytics/top-papers"),
        ("GET", "/analytics/topics"),
        ("GET", "/analytics/trends"),
        ("POST", "/projects"),
        ("GET", "/projects"),
        ("GET", "/projects/{project_id}"),
        ("PATCH", "/projects/{project_id}"),
        ("DELETE", "/projects/{project_id}"),
        ("GET", "/projects/{project_id}/recommendations"),
        ("POST", "/projects/{project_id}/reading-list"),
        ("GET", "/projects/{project_id}/reading-list"),
        ("PATCH", "/reading-list-items/{item_id}"),
        ("DELETE", "/reading-list-items/{item_id}"),
        ("GET", "/annotations/{annotation_id}"),
        ("PATCH", "/annotations/{annotation_id}"),
        ("DELETE", "/annotations/{annotation_id}"),
    }

    assert actual_routes == expected_routes
    assert ("GET", "/analytics/collaborations") not in actual_routes
    assert ("GET", "/") not in actual_routes


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/authors/search", {"query": ""}),
        ("/papers/search", {"year": -1}),
        ("/papers/https://openalex.org/W1/similar", {"limit": 0}),
        ("/papers/https://openalex.org/W1/citations", {"offset": -1}),
        (
            "/papers/https://openalex.org/W1/path/https://openalex.org/W2",
            {"max_depth": 13},
        ),
        ("/topics", {"limit": 0}),
        ("/topics/topic:computer-vision/papers", {"offset": -1}),
        ("/analytics/top-papers", {"limit": 0}),
        ("/analytics/topics", {"year": -1}),
        ("/analytics/trends", {"start_year": -1}),
    ],
)
def test_public_endpoint_validation_edges_return_422(
    client: TestClient,
    path: str,
    params: dict[str, int | str],
) -> None:
    response = client.get(path, params=params)
    assert response.status_code == 422


def test_discovery_edge_cases_cover_missing_resources_and_id_search(
    client: TestClient,
) -> None:
    author_search_by_id = client.get(
        "/authors/search",
        params={"query": "https://openalex.org/A1"},
    )
    author_papers_missing = client.get("/authors/https://openalex.org/A999/papers")

    assert author_search_by_id.status_code == 200
    assert [author["id"] for author in author_search_by_id.json()] == [
        "https://openalex.org/A1"
    ]
    assert author_papers_missing.status_code == 404
    assert (
        author_papers_missing.json()["detail"]
        == "author 'https://openalex.org/A999' was not found"
    )


def test_auth_validation_edges(client: TestClient) -> None:
    register_short_password = client.post(
        "/auth/register",
        json={"email": "edge@example.com", "password": "short"},
    )
    login_short_password = client.post(
        "/auth/login",
        json={"email": "edge@example.com", "password": "short"},
    )
    me_without_token = client.get("/auth/me")

    assert register_short_password.status_code == 422
    assert login_short_password.status_code == 422
    assert me_without_token.status_code == 401


def test_protected_endpoint_validation_and_not_found_edges(
    client: TestClient,
) -> None:
    headers = _register_user(client, "edge-owner@example.com")
    project_id = _create_project(client, headers)

    create_invalid_project = client.post(
        "/projects",
        json={"title": "", "description": "invalid"},
        headers=headers,
    )
    recommendations_invalid_mode = client.get(
        f"/projects/{project_id}/recommendations",
        params={"mode": "invalid"},
        headers=headers,
    )
    recommendations_weight_out_of_range = client.get(
        f"/projects/{project_id}/recommendations",
        params={"semantic_weight": 1.5},
        headers=headers,
    )
    recommendations_limit_invalid = client.get(
        f"/projects/{project_id}/recommendations",
        params={"limit": 0},
        headers=headers,
    )

    list_missing_project_reading_list = client.get(
        "/projects/missing-project/reading-list",
        headers=headers,
    )
    add_missing_project_reading_list = client.post(
        "/projects/missing-project/reading-list",
        json={"paper_id": "https://openalex.org/W1"},
        headers=headers,
    )

    annotation_text_invalid = client.post(
        "/papers/https://openalex.org/W1/annotations",
        json={"text": ""},
        headers=headers,
    )
    annotation_list_limit_invalid = client.get(
        "/papers/https://openalex.org/W1/annotations",
        params={"limit": 0},
        headers=headers,
    )

    missing_annotation_get = client.get("/annotations/missing-annotation", headers=headers)
    missing_annotation_patch = client.patch(
        "/annotations/missing-annotation",
        json={"text": "Updated"},
        headers=headers,
    )
    missing_annotation_delete = client.delete(
        "/annotations/missing-annotation",
        headers=headers,
    )

    missing_item_patch = client.patch(
        "/reading-list-items/missing-item",
        json={"priority": "high"},
        headers=headers,
    )
    missing_item_delete = client.delete("/reading-list-items/missing-item", headers=headers)

    assert create_invalid_project.status_code == 422
    assert recommendations_invalid_mode.status_code == 422
    assert recommendations_weight_out_of_range.status_code == 422
    assert recommendations_limit_invalid.status_code == 422

    assert list_missing_project_reading_list.status_code == 404
    assert add_missing_project_reading_list.status_code == 404

    assert annotation_text_invalid.status_code == 422
    assert annotation_list_limit_invalid.status_code == 422

    assert missing_annotation_get.status_code == 404
    assert missing_annotation_patch.status_code == 404
    assert missing_annotation_delete.status_code == 404
    assert missing_item_patch.status_code == 404
    assert missing_item_delete.status_code == 404
