from types import SimpleNamespace

from research_assistant_api.services.recommendations import RecommendationService


class AmbiguousEmbedding(list):
    def __bool__(self) -> bool:
        raise ValueError("ambiguous truth value")


class _ProjectRepository:
    def get_for_user(self, project_id: str, user_id: str) -> object | None:
        return SimpleNamespace(id=project_id, user_id=user_id)


class _ReadingListRepository:
    def __init__(self, reading_items: list[object]):
        self._reading_items = reading_items

    def list_for_project(self, project_id: str) -> list[object]:
        return self._reading_items


class _SimilarityRepository:
    def __init__(self, semantic_records: list[object]):
        self._semantic_records = semantic_records

    def list_by_embedding(
        self,
        target_embedding: list[float],
        *,
        exclude_paper_ids: set[str],
        limit: int,
        offset: int,
    ) -> list[object]:
        return self._semantic_records


class _CitationRepository:
    def __init__(self, papers_by_id: dict[str, object]):
        self._papers_by_id = papers_by_id

    def list_adjacent_paper_ids(
        self,
        source_paper_ids: list[str],
        *,
        exclude_paper_ids: set[str],
    ) -> set[str]:
        return set()

    def list_papers_by_ids(self, paper_ids: list[str]) -> list[object]:
        return [self._papers_by_id[paper_id] for paper_id in paper_ids if paper_id in self._papers_by_id]

    def list_connections_between(
        self,
        source_paper_ids: list[str],
        candidate_paper_ids: list[str],
    ) -> list[tuple[str, str]]:
        return []


def test_recommendations_handle_ambiguous_embedding_truth_values() -> None:
    reading_paper = SimpleNamespace(
        id="https://openalex.org/W-reading",
        title="Reading Paper",
        publication_year=2024,
        publication_date=None,
        citation_count=10,
        doi=None,
        journal=None,
        language=None,
        work_type=None,
        topic=None,
        embedding=AmbiguousEmbedding([1.0, 0.0, 0.0]),
    )
    candidate_paper = SimpleNamespace(
        id="https://openalex.org/W-candidate",
        title="Candidate Paper",
        publication_year=2023,
        publication_date=None,
        citation_count=5,
        doi=None,
        journal=None,
        language=None,
        work_type=None,
        topic=None,
        embedding=AmbiguousEmbedding([0.9, 0.1, 0.0]),
    )

    service = RecommendationService(
        project_repository=_ProjectRepository(),
        reading_list_repository=_ReadingListRepository(
            [
                SimpleNamespace(
                    paper_id=reading_paper.id,
                    paper=reading_paper,
                )
            ]
        ),
        similarity_repository=_SimilarityRepository(
            [SimpleNamespace(paper=candidate_paper, similarity_score=0.95)]
        ),
        citation_repository=_CitationRepository({candidate_paper.id: candidate_paper}),
    )

    response = service.list_project_recommendations(
        current_user=SimpleNamespace(id="user-1"),
        project_id="project-1",
        scoring_mode="hybrid",
        semantic_weight=None,
        citation_weight=None,
        limit=10,
        offset=0,
    )

    assert [item.id for item in response] == [candidate_paper.id]
    assert response[0].recommendation_score >= 0
