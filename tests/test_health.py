from fastapi.testclient import TestClient

from research_assistant_api.main import create_app


def test_application_starts_and_serves_health(monkeypatch) -> None:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")

    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert app.title == "Research Assistant API"
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Research Assistant API",
        "environment": "test",
    }
