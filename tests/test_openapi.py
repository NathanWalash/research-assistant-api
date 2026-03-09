from fastapi.testclient import TestClient

from research_assistant_api.main import API_DESCRIPTION, create_app


def test_openapi_exposes_core_metadata_and_routes() -> None:
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"] == "Research Assistant API"
    assert payload["info"]["description"] == API_DESCRIPTION
    assert "/projects/{project_id}/recommendations" in payload["paths"]
    assert "/papers/{paper_id}/similar" in payload["paths"]
