from collections import defaultdict
from dataclasses import dataclass
from math import sqrt
from typing import Literal

from research_assistant_api.embeddings import cosine_similarity
from research_assistant_api.models import Paper
from research_assistant_api.models import ReadingListItem, User
from research_assistant_api.repositories.citation_repository import CitationRepository
from research_assistant_api.repositories.project_repository import ProjectRepository
from research_assistant_api.repositories.reading_list_repository import (
    ReadingListRepository,
)
from research_assistant_api.repositories.similarity_repository import SimilarityRepository
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


class InvalidRecommendationWeightsError(Exception):
    def __init__(self):
        super().__init__("semantic_weight and citation_weight cannot both be zero")


@dataclass(frozen=True, slots=True)
class RecommendationScoring:
    mode: Literal["semantic", "citation", "hybrid"]
    semantic_weight: float
    citation_weight: float


@dataclass(frozen=True, slots=True)
class RecommendationCandidate:
    paper: Paper
    semantic_score: float
    citation_score: float
    recommendation_score: float


def _build_topic_summary(topic: object | None) -> TopicSummary | None:
    if topic is None:
        return None
    return TopicSummary.model_validate(topic)


def _build_recommendation_response(
    candidate: RecommendationCandidate,
    scoring: RecommendationScoring,
) -> ProjectRecommendationResponse:
    paper = candidate.paper
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
        recommendation_score=round(candidate.recommendation_score, 6),
        semantic_score=round(candidate.semantic_score, 6),
        citation_score=round(candidate.citation_score, 6),
        scoring_mode=scoring.mode,
        semantic_weight=round(scoring.semantic_weight, 6),
        citation_weight=round(scoring.citation_weight, 6),
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


def _resolve_scoring(
    *,
    scoring_mode: Literal["semantic", "citation", "hybrid"],
    semantic_weight: float | None,
    citation_weight: float | None,
) -> RecommendationScoring:
    default_weights = {
        "semantic": (1.0, 0.0),
        "citation": (0.0, 1.0),
        "hybrid": (0.7, 0.3),
    }
    resolved_semantic_weight, resolved_citation_weight = default_weights[scoring_mode]

    if semantic_weight is not None:
        resolved_semantic_weight = semantic_weight
    if citation_weight is not None:
        resolved_citation_weight = citation_weight

    total_weight = resolved_semantic_weight + resolved_citation_weight
    if total_weight <= 0:
        raise InvalidRecommendationWeightsError

    return RecommendationScoring(
        mode=scoring_mode,
        semantic_weight=resolved_semantic_weight / total_weight,
        citation_weight=resolved_citation_weight / total_weight,
    )


def _build_citation_scores(
    *,
    source_paper_ids: set[str],
    candidate_paper_ids: set[str],
    citation_repository: CitationRepository,
) -> dict[str, float]:
    if not source_paper_ids or not candidate_paper_ids:
        return {}

    connected_source_papers_by_candidate: dict[str, set[str]] = defaultdict(set)
    for citing_paper_id, cited_paper_id in citation_repository.list_connections_between(
        sorted(source_paper_ids),
        sorted(candidate_paper_ids),
    ):
        if citing_paper_id in source_paper_ids and cited_paper_id in candidate_paper_ids:
            connected_source_papers_by_candidate[cited_paper_id].add(citing_paper_id)
        elif cited_paper_id in source_paper_ids and citing_paper_id in candidate_paper_ids:
            connected_source_papers_by_candidate[citing_paper_id].add(cited_paper_id)

    source_count = len(source_paper_ids)
    return {
        candidate_paper_id: len(connected_source_papers) / source_count
        for candidate_paper_id, connected_source_papers in connected_source_papers_by_candidate.items()
    }


class RecommendationService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        reading_list_repository: ReadingListRepository,
        similarity_repository: SimilarityRepository,
        citation_repository: CitationRepository,
    ):
        self.project_repository = project_repository
        self.reading_list_repository = reading_list_repository
        self.similarity_repository = similarity_repository
        self.citation_repository = citation_repository

    def list_project_recommendations(
        self,
        current_user: User,
        project_id: str,
        *,
        scoring_mode: Literal["semantic", "citation", "hybrid"],
        semantic_weight: float | None,
        citation_weight: float | None,
        limit: int,
        offset: int,
    ) -> list[ProjectRecommendationResponse]:
        project = self.project_repository.get_for_user(project_id, current_user.id)
        if project is None:
            raise ProjectNotFoundError(project_id)

        reading_list_items = self.reading_list_repository.list_for_project(project_id)
        excluded_paper_ids = {item.paper_id for item in reading_list_items}
        project_paper_ids = excluded_paper_ids.copy()
        scoring = _resolve_scoring(
            scoring_mode=scoring_mode,
            semantic_weight=semantic_weight,
            citation_weight=citation_weight,
        )

        project_embedding = _build_project_embedding(reading_list_items)
        if project_embedding is None and scoring.semantic_weight > 0:
            raise ProjectRecommendationsUnavailableError(project_id)

        semantic_candidate_papers: dict[str, Paper] = {}
        if project_embedding is not None:
            semantic_records = self.similarity_repository.list_by_embedding(
                project_embedding,
                exclude_paper_ids=excluded_paper_ids,
                limit=max((limit + offset) * 10, 200),
                offset=0,
            )
            semantic_candidate_papers = {
                record.paper.id: record.paper for record in semantic_records
            }

        citation_candidate_ids = self.citation_repository.list_adjacent_paper_ids(
            sorted(project_paper_ids),
            exclude_paper_ids=excluded_paper_ids,
        )
        candidate_ids = set(semantic_candidate_papers) | citation_candidate_ids
        candidate_papers = {
            paper.id: paper
            for paper in self.citation_repository.list_papers_by_ids(sorted(candidate_ids))
        }

        citation_scores = _build_citation_scores(
            source_paper_ids=project_paper_ids,
            candidate_paper_ids=set(candidate_papers),
            citation_repository=self.citation_repository,
        )
        ranked_candidates = sorted(
            (
                RecommendationCandidate(
                    paper=paper,
                    semantic_score=(
                        cosine_similarity(project_embedding, paper.embedding)
                        if project_embedding is not None and paper.embedding is not None
                        else 0.0
                    ),
                    citation_score=citation_scores.get(paper_id, 0.0),
                    recommendation_score=0.0,
                )
                for paper_id, paper in candidate_papers.items()
            ),
            key=lambda candidate: (
                -(
                    scoring.semantic_weight * candidate.semantic_score
                    + scoring.citation_weight * candidate.citation_score
                ),
                -candidate.citation_score,
                -candidate.paper.citation_count,
                -candidate.paper.publication_year,
                candidate.paper.title,
            ),
        )

        scored_candidates: list[RecommendationCandidate] = []
        for candidate in ranked_candidates:
            raw_recommendation_score = (
                scoring.semantic_weight * candidate.semantic_score
                + scoring.citation_weight * candidate.citation_score
            )
            scored_candidates.append(
                RecommendationCandidate(
                    paper=candidate.paper,
                    semantic_score=candidate.semantic_score,
                    citation_score=candidate.citation_score,
                    recommendation_score=max(raw_recommendation_score, 0.0),
                )
            )
        return [
            _build_recommendation_response(candidate, scoring)
            for candidate in scored_candidates[offset : offset + limit]
        ]
