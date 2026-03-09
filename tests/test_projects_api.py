import pytest
from fastapi.testclient import TestClient

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine
from research_assistant_api.main import create_app


@pytest.fixture
def client(sqlite_database_url: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "RESEARCH_API_JWT_SECRET_KEY",
        "test-secret-key-with-32-byte-minimum",
    )
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)
    return TestClient(create_app())


def _register_user(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password"},
    )
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_project_create_list_and_get_workflow(client: TestClient) -> None:
    headers = _register_user(client, "owner@example.com")

    create_response = client.post(
        "/projects",
        json={"title": " Dissertation Plan ", "description": "Primary notes"},
        headers=headers,
    )
    project_id = create_response.json()["id"]

    list_response = client.get("/projects", headers=headers)
    detail_response = client.get(f"/projects/{project_id}", headers=headers)

    assert create_response.status_code == 201
    assert create_response.json()["title"] == "Dissertation Plan"
    assert list_response.status_code == 200
    assert [project["id"] for project in list_response.json()] == [project_id]
    assert detail_response.status_code == 200
    assert detail_response.json()["description"] == "Primary notes"


def test_project_update_and_delete_workflow(client: TestClient) -> None:
    headers = _register_user(client, "owner@example.com")
    create_response = client.post(
        "/projects",
        json={"title": "Draft", "description": "Old notes"},
        headers=headers,
    )
    project_id = create_response.json()["id"]

    update_response = client.patch(
        f"/projects/{project_id}",
        json={"title": "Final Draft", "description": "Updated notes"},
        headers=headers,
    )
    delete_response = client.delete(f"/projects/{project_id}", headers=headers)
    get_after_delete = client.get(f"/projects/{project_id}", headers=headers)

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Final Draft"
    assert update_response.json()["description"] == "Updated notes"
    assert delete_response.status_code == 204
    assert get_after_delete.status_code == 404


def test_projects_require_authentication(client: TestClient) -> None:
    response = client.get("/projects")

    assert response.status_code == 401


def test_project_routes_enforce_ownership(client: TestClient) -> None:
    owner_headers = _register_user(client, "owner@example.com")
    other_headers = _register_user(client, "other@example.com")

    create_response = client.post(
        "/projects",
        json={"title": "Owner Project", "description": None},
        headers=owner_headers,
    )
    project_id = create_response.json()["id"]

    detail_response = client.get(f"/projects/{project_id}", headers=other_headers)
    update_response = client.patch(
        f"/projects/{project_id}",
        json={"title": "Hijacked"},
        headers=other_headers,
    )
    delete_response = client.delete(f"/projects/{project_id}", headers=other_headers)

    assert detail_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    assert detail_response.json()["detail"] == f"project '{project_id}' was not found"
