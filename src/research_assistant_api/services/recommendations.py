from math import sqrt

from research_assistant_api.models import ReadingListItem, User
from research_assistant_api.repositories.project_repository import ProjectRepository
from research_assistant_api.repositories.reading_list_repository import (
    ReadingListRepository,
)
from research_assistant_api.repositories.similarity_repository import (
    ScoredPaperRecord,
    SimilarityRepository,
)
from research_assistant_api.schemas.discovery import TopicSummary
from research_assistant_api.schemas.recommendations import (
    ProjectRecommendationResponse,
)
from research_assistant_api.services.projects import ProjectNotFoundError


class ProjectRecommendationsUnavailableError(Exception):
    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(
            f"project '{project_id}' does not have any embedded reading list papers yet"
        )


def _build_topic_summary(topic: object | None) -> TopicSummary | None:
    if topic is None:
        return None
    return TopicSummary.model_validate(topic)


def _build_recommendation_response(
    record: ScoredPaperRecord,
) -> ProjectRecommendationResponse:
    paper = record.paper
    return ProjectRecommendationResponse(
        id=paper.id,
        title=paper.title,
        publication_year=paper.publication_year,
        publication_date=paper.publication_date,
        citation_count=paper.citation_count,
        doi=paper.doi,
        journal=paper.journal,
        language=paper.language,
        work_type=paper.work_type,
        topic=_build_topic_summary(paper.topic),
        recommendation_score=round(record.similarity_score, 6),
    )


def _normalize_embedding(values: list[float]) -> list[float]:
    magnitude = sqrt(sum(value * value for value in values))
    if magnitude == 0.0:
        return values
    return [value / magnitude for value in values]


def _build_project_embedding(reading_list_items: list[ReadingListItem]) -> list[float] | None:
    embedded_papers = [
        item.paper.embedding
        for item in reading_list_items
        if item.paper is not None and item.paper.embedding is not None
    ]
    if not embedded_papers:
        return None

    dimension = len(embedded_papers[0])
    averaged = [
        sum(embedding[index] for embedding in embedded_papers) / len(embedded_papers)
        for index in range(dimension)
    ]
    return _normalize_embedding(averaged)


class RecommendationService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        reading_list_repository: ReadingListRepository,
        similarity_repository: SimilarityRepository,
    ):
        self.project_repository = project_repository
        self.reading_list_repository = reading_list_repository
        self.similarity_repository = similarity_repository

    def list_project_recommendations(
        self,
        current_user: User,
        project_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[ProjectRecommendationResponse]:
        project = self.project_repository.get_for_user(project_id, current_user.id)
        if project is None:
            raise ProjectNotFoundError(project_id)

        reading_list_items = self.reading_list_repository.list_for_project(project_id)
        project_embedding = _build_project_embedding(reading_list_items)
        if project_embedding is None:
            raise ProjectRecommendationsUnavailableError(project_id)

        excluded_paper_ids = {item.paper_id for item in reading_list_items}
        recommendation_records = self.similarity_repository.list_by_embedding(
            project_embedding,
            exclude_paper_ids=excluded_paper_ids,
            limit=limit,
            offset=offset,
        )
        return [_build_recommendation_response(record) for record in recommendation_records]
