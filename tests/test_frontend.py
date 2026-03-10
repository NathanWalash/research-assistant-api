from fastapi.testclient import TestClient

from research_assistant_api.main import create_app


def test_frontend_pages_are_served(monkeypatch) -> None:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")

    app = create_app()
    client = TestClient(app)

    for path in [
        "/app",
        "/app/",
        "/app/login",
        "/app/register",
        "/app/discover",
        "/app/endpoints",
        "/app/projects",
        "/app/analytics",
        "/app/account",
    ]:
        response = client.get(path)

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "/app/static/app.css" in response.text


def test_frontend_static_assets_are_served(monkeypatch) -> None:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")

    app = create_app()
    client = TestClient(app)

    for path in [
        "/app/static/app.css",
        "/app/static/main.js",
    ]:
        response = client.get(path)

        assert response.status_code == 200


def test_unknown_frontend_page_returns_404(monkeypatch) -> None:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")

    app = create_app()
    client = TestClient(app)

    response = client.get("/app/unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "frontend page was not found"}
