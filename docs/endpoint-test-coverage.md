# Endpoint Test Coverage Matrix

This matrix maps every public API endpoint in the OpenAPI contract to automated test coverage in this repository.

## Coverage Principles

- `tests/test_api_coverage_api.py` is the route-inventory gate. It asserts the OpenAPI route set exactly matches the expected endpoint contract.
- Feature-specific tests then validate behavior, not just existence: happy path, validation edges, authorization, ownership boundaries, and not-found handling.
- CI runs this full test suite on every push and pull request.

## Route Coverage Matrix

| Method | Endpoint | Primary Test Coverage |
| --- | --- | --- |
| `GET` | `/health` | `tests/test_health.py` |
| `POST` | `/auth/register` | `tests/test_auth_api.py`, `tests/test_api_coverage_api.py` |
| `POST` | `/auth/login` | `tests/test_auth_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/auth/me` | `tests/test_auth_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/papers/search` | `tests/test_discovery_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/papers/{paper_id}` | `tests/test_discovery_api.py` |
| `GET` | `/papers/{paper_id}/similar` | `tests/test_similarity_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/papers/{paper_id}/citations` | `tests/test_citation_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/papers/{paper_id}/path/{target_paper_id}` | `tests/test_citation_api.py`, `tests/test_api_coverage_api.py` |
| `POST` | `/papers/{paper_id}/annotations` | `tests/test_annotations_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/papers/{paper_id}/annotations` | `tests/test_annotations_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/authors` | `tests/test_discovery_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/authors/search` | `tests/test_discovery_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/authors/{author_id}` | `tests/test_discovery_api.py` |
| `GET` | `/authors/{author_id}/papers` | `tests/test_discovery_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/topics` | `tests/test_discovery_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/topics/{topic_id}/papers` | `tests/test_discovery_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/analytics/top-papers` | `tests/test_analytics_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/analytics/topics` | `tests/test_analytics_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/analytics/trends` | `tests/test_analytics_api.py`, `tests/test_api_coverage_api.py` |
| `POST` | `/projects` | `tests/test_projects_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/projects` | `tests/test_projects_api.py` |
| `GET` | `/projects/{project_id}` | `tests/test_projects_api.py` |
| `PATCH` | `/projects/{project_id}` | `tests/test_projects_api.py` |
| `DELETE` | `/projects/{project_id}` | `tests/test_projects_api.py` |
| `GET` | `/projects/{project_id}/recommendations` | `tests/test_recommendations_api.py`, `tests/test_api_coverage_api.py` |
| `POST` | `/projects/{project_id}/reading-list` | `tests/test_reading_list_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/projects/{project_id}/reading-list` | `tests/test_reading_list_api.py`, `tests/test_api_coverage_api.py` |
| `PATCH` | `/reading-list-items/{item_id}` | `tests/test_reading_list_api.py`, `tests/test_api_coverage_api.py` |
| `DELETE` | `/reading-list-items/{item_id}` | `tests/test_reading_list_api.py`, `tests/test_api_coverage_api.py` |
| `GET` | `/annotations/{annotation_id}` | `tests/test_annotations_api.py`, `tests/test_api_coverage_api.py` |
| `PATCH` | `/annotations/{annotation_id}` | `tests/test_annotations_api.py`, `tests/test_api_coverage_api.py` |
| `DELETE` | `/annotations/{annotation_id}` | `tests/test_annotations_api.py`, `tests/test_api_coverage_api.py` |

## Deliberately Excluded Endpoint

- `GET /analytics/collaborations` is intentionally not part of the API contract. It was removed due to poor interactive performance at this dataset size.

