from fastapi.testclient import TestClient

from research_assistant_api.main import API_DESCRIPTION, create_app


def test_openapi_exposes_core_metadata_and_routes() -> None:
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"] == "Research Assistant API"
    assert payload["info"]["description"] == API_DESCRIPTION
    tags = {tag["name"]: tag["description"] for tag in payload["tags"]}
    assert "papers" in tags
    assert "annotations" in tags
    assert "/projects/{project_id}/recommendations" in payload["paths"]
    assert "/papers/{paper_id}/citations" in payload["paths"]
    assert "/papers/{paper_id}/path/{target_paper_id}" in payload["paths"]
    assert "/papers/{paper_id}/similar" in payload["paths"]
    assert "/papers/{paper_id}/annotations" in payload["paths"]
    assert "/annotations/{annotation_id}" in payload["paths"]
    assert (
        payload["paths"]["/projects/{project_id}/recommendations"]["get"]["summary"]
        == "List project recommendations"
    )
