from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.main import create_app
from research_assistant_api.models import Citation
from research_assistant_api.models import Paper

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

        paper_one = session.get(Paper, "https://openalex.org/W1")
        paper_two = session.get(Paper, "https://openalex.org/W2")
        assert paper_one is not None
        assert paper_two is not None
        paper_one.embedding = [1.0, 0.0, 0.0]
        paper_two.embedding = [0.8, 0.2, 0.0]

        session.add_all(
            [
                Paper(
                    id="https://openalex.org/W3",
                    title="Recommended Paper One",
                    abstract="Closest match",
                    publication_year=2024,
                    citation_count=5,
                    embedding=[0.95, 0.05, 0.0],
                ),
                Paper(
                    id="https://openalex.org/W4",
                    title="Recommended Paper Two",
                    abstract="Second closest match",
                    publication_year=2023,
                    citation_count=50,
                    embedding=[0.7, 0.3, 0.0],
                ),
                Paper(
                    id="https://openalex.org/W5",
                    title="Lower Ranked Paper",
                    abstract="Much weaker match",
                    publication_year=2022,
                    citation_count=100,
                    embedding=[0.0, 1.0, 0.0],
                ),
                Paper(
                    id="https://openalex.org/W6",
                    title="Not Embedded Yet",
                    abstract="Missing embedding context",
                    publication_year=2024,
                    citation_count=1,
                ),
            ]
        )
        session.add_all(
            [
                Citation(
                    citing_paper_id="https://openalex.org/W3",
                    cited_paper_id="https://openalex.org/W1",
                ),
                Citation(
                    citing_paper_id="https://openalex.org/W4",
                    cited_paper_id="https://openalex.org/W1",
                ),
                Citation(
                    citing_paper_id="https://openalex.org/W2",
                    cited_paper_id="https://openalex.org/W4",
                ),
            ]
        )
        session.commit()


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
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def _create_project(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/projects",
        json={"title": "Recommendations", "description": "Project context"},
        headers=headers,
    )
    return response.json()["id"]


def _add_project_paper(
    client: TestClient,
    project_id: str,
    paper_id: str,
    headers: dict[str, str],
) -> None:
    response = client.post(
        f"/projects/{project_id}/reading-list",
        json={"paper_id": paper_id},
        headers=headers,
    )
    assert response.status_code == 201


def test_project_recommendations_rank_candidates_and_exclude_reading_list(
    client: TestClient,
) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)
    _add_project_paper(client, project_id, "https://openalex.org/W1", headers)
    _add_project_paper(client, project_id, "https://openalex.org/W2", headers)

    response = client.get(
        f"/projects/{project_id}/recommendations",
        params={"limit": 2},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [
        "https://openalex.org/W4",
        "https://openalex.org/W3",
    ]
    assert payload[0]["recommendation_score"] > payload[1]["recommendation_score"]
    assert payload[0]["scoring_mode"] == "hybrid"
    assert payload[0]["semantic_weight"] == 0.7
    assert payload[0]["citation_weight"] == 0.3


def test_project_recommendations_support_semantic_only_mode(
    client: TestClient,
) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)
    _add_project_paper(client, project_id, "https://openalex.org/W1", headers)
    _add_project_paper(client, project_id, "https://openalex.org/W2", headers)

    response = client.get(
        f"/projects/{project_id}/recommendations",
        params={"mode": "semantic", "limit": 2},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [
        "https://openalex.org/W3",
        "https://openalex.org/W4",
    ]
    assert payload[0]["semantic_weight"] == 1.0
    assert payload[0]["citation_weight"] == 0.0


def test_project_recommendations_support_citation_only_mode(
    client: TestClient,
) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)
    _add_project_paper(client, project_id, "https://openalex.org/W1", headers)
    _add_project_paper(client, project_id, "https://openalex.org/W2", headers)

    response = client.get(
        f"/projects/{project_id}/recommendations",
        params={"mode": "citation", "limit": 2},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [
        "https://openalex.org/W4",
        "https://openalex.org/W3",
    ]
    assert payload[0]["citation_weight"] == 1.0
    assert payload[0]["semantic_weight"] == 0.0


def test_project_recommendations_support_custom_weights(
    client: TestClient,
) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)
    _add_project_paper(client, project_id, "https://openalex.org/W1", headers)
    _add_project_paper(client, project_id, "https://openalex.org/W2", headers)

    response = client.get(
        f"/projects/{project_id}/recommendations",
        params={
            "mode": "hybrid",
            "semantic_weight": 0.9,
            "citation_weight": 0.1,
            "limit": 2,
        },
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [
        "https://openalex.org/W4",
        "https://openalex.org/W3",
    ]
    assert payload[0]["semantic_weight"] == 0.9
    assert payload[0]["citation_weight"] == 0.1


def test_project_recommendations_require_embedded_context(client: TestClient) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)
    _add_project_paper(client, project_id, "https://openalex.org/W6", headers)

    response = client.get(f"/projects/{project_id}/recommendations", headers=headers)

    assert response.status_code == 409
    assert response.json()["detail"] == (
        f"project '{project_id}' does not have any embedded reading list papers yet"
    )


def test_project_recommendations_allow_citation_mode_without_embeddings(
    client: TestClient,
) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)
    _add_project_paper(client, project_id, "https://openalex.org/W6", headers)

    response = client.get(
        f"/projects/{project_id}/recommendations",
        params={"mode": "citation"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_project_recommendations_citation_mode_returns_ranked_candidates_without_edges(
    client: TestClient,
) -> None:
    headers = _register_user(client, "owner-citation@example.com")
    project_id = _create_project(client, headers)
    _add_project_paper(client, project_id, "https://openalex.org/W5", headers)

    response = client.get(
        f"/projects/{project_id}/recommendations",
        params={"mode": "citation", "limit": 3},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all(item["id"] != "https://openalex.org/W5" for item in payload)
    assert all(item["scoring_mode"] == "citation" for item in payload)
    assert all(item["citation_score"] == 0.0 for item in payload)
    assert all(item["recommendation_score"] == 0.0 for item in payload)


def test_project_recommendations_require_authentication(client: TestClient) -> None:
    response = client.get("/projects/project-1/recommendations")

    assert response.status_code == 401


def test_project_recommendations_enforce_ownership(client: TestClient) -> None:
    owner_headers = _register_user(client, "owner@example.com")
    other_headers = _register_user(client, "other@example.com")
    project_id = _create_project(client, owner_headers)
    _add_project_paper(client, project_id, "https://openalex.org/W1", owner_headers)

    response = client.get(
        f"/projects/{project_id}/recommendations",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == f"project '{project_id}' was not found"


def test_project_recommendations_reject_zero_total_weights(
    client: TestClient,
) -> None:
    headers = _register_user(client, "owner@example.com")
    project_id = _create_project(client, headers)
    _add_project_paper(client, project_id, "https://openalex.org/W1", headers)

    response = client.get(
        f"/projects/{project_id}/recommendations",
        params={"semantic_weight": 0, "citation_weight": 0},
        headers=headers,
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "semantic_weight and citation_weight cannot both be zero"
    )
