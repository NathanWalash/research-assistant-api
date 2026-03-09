from research_assistant_api.repositories.similarity_repository import (
    SimilarPaperRecord,
    SimilarityRepository,
)
from research_assistant_api.schemas.discovery import TopicSummary
from research_assistant_api.schemas.similarity import SimilarPaperResponse
from research_assistant_api.services.discovery import DiscoveryNotFoundError


class PaperEmbeddingNotAvailableError(Exception):
    def __init__(self, paper_id: str):
        self.paper_id = paper_id
        super().__init__(f"paper '{paper_id}' does not have an embedding yet")


def _build_topic_summary(topic: object | None) -> TopicSummary | None:
    if topic is None:
        return None
    return TopicSummary.model_validate(topic)


def _build_similar_paper_response(record: SimilarPaperRecord) -> SimilarPaperResponse:
    paper = record.paper
    return SimilarPaperResponse(
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
        similarity_score=round(record.similarity_score, 6),
    )


class SimilarityService:
    def __init__(self, repository: SimilarityRepository):
        self.repository = repository

    def list_similar_papers(
        self,
        paper_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[SimilarPaperResponse]:
        target_paper = self.repository.get_by_id(paper_id)
        if target_paper is None:
            raise DiscoveryNotFoundError("paper", paper_id)
        if target_paper.embedding is None:
            raise PaperEmbeddingNotAvailableError(paper_id)

        similar_records = self.repository.list_similar(
            target_paper,
            limit=limit,
            offset=offset,
        )
        return [_build_similar_paper_response(record) for record in similar_records]
