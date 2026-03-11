from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from research_assistant_api.db.base import Base
from research_assistant_api.db.session import get_engine, get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService
from research_assistant_api.main import create_app
from research_assistant_api.models import Paper

FIXTURES_DIR = Path(__file__).parent / "fixtures"

EXPECTED_ROUTES = {
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


def _seed_dataset(database_url: str) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = get_session_factory(database_url)
    config = IngestionConfig(
        csv_path=FIXTURES_DIR / "sample_openalex_leeds_graph.csv",
        citation_csv_path=FIXTURES_DIR / "sample_citation_graph_edges.csv",
        batch_size=10,
    )

    with session_factory() as session:
        CsvIngestionService(session).ingest(config)
        papers = {
            paper.id: paper
            for paper in session.scalars(select(Paper)).all()
        }
        papers["https://openalex.org/W1"].embedding = [1.0, 0.0, 0.0]
        papers["https://openalex.org/W2"].embedding = [0.8, 0.2, 0.0]
        papers["https://openalex.org/W3"].embedding = [0.75, 0.25, 0.0]
        papers["https://openalex.org/W4"].embedding = [0.6, 0.4, 0.0]
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


def test_endpoint_smoke_matrix_covers_full_api_contract(
    client: TestClient,
) -> None:
    covered_routes: set[tuple[str, str]] = set()

    health = client.get("/health")
    covered_routes.add(("GET", "/health"))
    assert health.status_code == 200

    register = client.post(
        "/auth/register",
        json={"email": "matrix@example.com", "password": "strong-password"},
    )
    covered_routes.add(("POST", "/auth/register"))
    assert register.status_code == 201
    access_token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    login = client.post(
        "/auth/login",
        json={"email": "matrix@example.com", "password": "strong-password"},
    )
    covered_routes.add(("POST", "/auth/login"))
    assert login.status_code == 200

    me = client.get("/auth/me", headers=headers)
    covered_routes.add(("GET", "/auth/me"))
    assert me.status_code == 200

    search = client.get("/papers/search", params={"query": "Paper", "limit": 2})
    covered_routes.add(("GET", "/papers/search"))
    assert search.status_code == 200
    assert search.json()
    paper_id = search.json()[0]["id"]

    paper_detail = client.get(f"/papers/{paper_id}")
    covered_routes.add(("GET", "/papers/{paper_id}"))
    assert paper_detail.status_code == 200

    similar = client.get(f"/papers/{paper_id}/similar", params={"limit": 2})
    covered_routes.add(("GET", "/papers/{paper_id}/similar"))
    assert similar.status_code == 200

    citations = client.get(f"/papers/{paper_id}/citations", params={"limit": 2})
    covered_routes.add(("GET", "/papers/{paper_id}/citations"))
    assert citations.status_code == 200

    citation_path = client.get(
        "/papers/https://openalex.org/W3/path/https://openalex.org/W1"
    )
    covered_routes.add(("GET", "/papers/{paper_id}/path/{target_paper_id}"))
    assert citation_path.status_code == 200

    authors = client.get("/authors", params={"limit": 2})
    covered_routes.add(("GET", "/authors"))
    assert authors.status_code == 200
    assert authors.json()
    author_id = authors.json()[0]["id"]

    author_search = client.get("/authors/search", params={"query": "alice"})
    covered_routes.add(("GET", "/authors/search"))
    assert author_search.status_code == 200

    author_detail = client.get(f"/authors/{author_id}")
    covered_routes.add(("GET", "/authors/{author_id}"))
    assert author_detail.status_code == 200

    author_papers = client.get(f"/authors/{author_id}/papers")
    covered_routes.add(("GET", "/authors/{author_id}/papers"))
    assert author_papers.status_code == 200

    topics = client.get("/topics", params={"limit": 2})
    covered_routes.add(("GET", "/topics"))
    assert topics.status_code == 200
    assert topics.json()
    topic_id = topics.json()[0]["id"]

    topic_papers = client.get(f"/topics/{topic_id}/papers")
    covered_routes.add(("GET", "/topics/{topic_id}/papers"))
    assert topic_papers.status_code == 200

    top_papers = client.get("/analytics/top-papers", params={"limit": 2})
    covered_routes.add(("GET", "/analytics/top-papers"))
    assert top_papers.status_code == 200

    topic_distribution = client.get("/analytics/topics", params={"limit": 2})
    covered_routes.add(("GET", "/analytics/topics"))
    assert topic_distribution.status_code == 200

    trends = client.get("/analytics/trends", params={"start_year": 2021})
    covered_routes.add(("GET", "/analytics/trends"))
    assert trends.status_code == 200

    create_project = client.post(
        "/projects",
        json={"title": "Matrix Project", "description": "End-to-end smoke"},
        headers=headers,
    )
    covered_routes.add(("POST", "/projects"))
    assert create_project.status_code == 201
    project_id = create_project.json()["id"]

    list_projects = client.get("/projects", headers=headers)
    covered_routes.add(("GET", "/projects"))
    assert list_projects.status_code == 200

    get_project = client.get(f"/projects/{project_id}", headers=headers)
    covered_routes.add(("GET", "/projects/{project_id}"))
    assert get_project.status_code == 200

    update_project = client.patch(
        f"/projects/{project_id}",
        json={"title": "Matrix Project Updated"},
        headers=headers,
    )
    covered_routes.add(("PATCH", "/projects/{project_id}"))
    assert update_project.status_code == 200

    add_item_one = client.post(
        f"/projects/{project_id}/reading-list",
        json={"paper_id": "https://openalex.org/W1", "priority": "high"},
        headers=headers,
    )
    covered_routes.add(("POST", "/projects/{project_id}/reading-list"))
    assert add_item_one.status_code == 201

    add_item_two = client.post(
        f"/projects/{project_id}/reading-list",
        json={"paper_id": "https://openalex.org/W2"},
        headers=headers,
    )
    assert add_item_two.status_code == 201
    reading_list_item_id = add_item_two.json()["id"]

    list_items = client.get(f"/projects/{project_id}/reading-list", headers=headers)
    covered_routes.add(("GET", "/projects/{project_id}/reading-list"))
    assert list_items.status_code == 200

    update_item = client.patch(
        f"/reading-list-items/{reading_list_item_id}",
        json={"priority": "low"},
        headers=headers,
    )
    covered_routes.add(("PATCH", "/reading-list-items/{item_id}"))
    assert update_item.status_code == 200

    recommendations = client.get(
        f"/projects/{project_id}/recommendations",
        params={"mode": "hybrid", "limit": 2},
        headers=headers,
    )
    covered_routes.add(("GET", "/projects/{project_id}/recommendations"))
    assert recommendations.status_code == 200

    create_annotation = client.post(
        "/papers/https://openalex.org/W1/annotations",
        json={"text": "Matrix note"},
        headers=headers,
    )
    covered_routes.add(("POST", "/papers/{paper_id}/annotations"))
    assert create_annotation.status_code == 201
    annotation_id = create_annotation.json()["id"]

    list_annotations = client.get(
        "/papers/https://openalex.org/W1/annotations",
        headers=headers,
    )
    covered_routes.add(("GET", "/papers/{paper_id}/annotations"))
    assert list_annotations.status_code == 200

    annotation_detail = client.get(f"/annotations/{annotation_id}", headers=headers)
    covered_routes.add(("GET", "/annotations/{annotation_id}"))
    assert annotation_detail.status_code == 200

    annotation_update = client.patch(
        f"/annotations/{annotation_id}",
        json={"text": "Updated matrix note"},
        headers=headers,
    )
    covered_routes.add(("PATCH", "/annotations/{annotation_id}"))
    assert annotation_update.status_code == 200

    annotation_delete = client.delete(f"/annotations/{annotation_id}", headers=headers)
    covered_routes.add(("DELETE", "/annotations/{annotation_id}"))
    assert annotation_delete.status_code == 204

    delete_item = client.delete(
        f"/reading-list-items/{reading_list_item_id}",
        headers=headers,
    )
    covered_routes.add(("DELETE", "/reading-list-items/{item_id}"))
    assert delete_item.status_code == 204

    delete_project = client.delete(f"/projects/{project_id}", headers=headers)
    covered_routes.add(("DELETE", "/projects/{project_id}"))
    assert delete_project.status_code == 204

    assert covered_routes == EXPECTED_ROUTES
