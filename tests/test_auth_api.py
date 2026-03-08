import pytest
from fastapi.testclient import TestClient

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine
from research_assistant_api.main import create_app


@pytest.fixture
def client(sqlite_database_url: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("RESEARCH_API_ENVIRONMENT", "test")
    monkeypatch.setenv("RESEARCH_API_JWT_SECRET_KEY", "test-secret-key")
    engine = get_engine(sqlite_database_url)
    Base.metadata.create_all(engine)
    return TestClient(create_app())


def test_register_returns_access_token_and_user_profile(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "User@Example.com", "password": "strong-password"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "user@example.com"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {"email": "user@example.com", "password": "strong-password"}

    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "user with email 'user@example.com' already exists"
    )


def test_login_returns_access_token_for_valid_credentials(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "strong-password"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "USER@example.com", "password": "strong-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "user@example.com"


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "strong-password"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


def test_auth_me_returns_current_user_for_valid_token(client: TestClient) -> None:
    register_response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "strong-password"},
    )
    access_token = register_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_auth_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid or expired access token"
