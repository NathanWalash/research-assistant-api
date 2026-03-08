from research_assistant_api.models import Paper
from research_assistant_api.repositories.analytics_repository import (
    AnalyticsRepository,
    CollaborationPairRecord,
    PublicationTrendRecord,
    TopicAnalyticsRecord,
)
from research_assistant_api.schemas.analytics import (
    AnalyticsPaperItem,
    CollaborationPairItem,
    PublicationTrendItem,
    TopicAnalyticsItem,
)
from research_assistant_api.schemas.discovery import TopicSummary


def _build_topic_summary(topic: object | None) -> TopicSummary | None:
    if topic is None:
        return None
    return TopicSummary.model_validate(topic)


def _build_analytics_paper_item(paper: Paper) -> AnalyticsPaperItem:
    return AnalyticsPaperItem(
        id=paper.id,
        title=paper.title,
        publication_year=paper.publication_year,
        citation_count=paper.citation_count,
        journal=paper.journal,
        topic=_build_topic_summary(paper.topic),
    )


def _build_topic_analytics_item(record: TopicAnalyticsRecord) -> TopicAnalyticsItem:
    return TopicAnalyticsItem(
        id=record.topic.id,
        name=record.topic.name,
        field=record.topic.field,
        paper_count=record.paper_count,
        total_citation_count=record.total_citation_count,
        average_citation_count=round(record.average_citation_count, 2),
    )


def _build_publication_trend_item(
    record: PublicationTrendRecord,
) -> PublicationTrendItem:
    return PublicationTrendItem(
        publication_year=record.publication_year,
        paper_count=record.paper_count,
        total_citation_count=record.total_citation_count,
        average_citation_count=round(record.average_citation_count, 2),
    )


def _build_collaboration_pair_item(
    record: CollaborationPairRecord,
) -> CollaborationPairItem:
    return CollaborationPairItem(
        author_a_id=record.author_a_id,
        author_a_name=record.author_a_name,
        author_b_id=record.author_b_id,
        author_b_name=record.author_b_name,
        shared_paper_count=record.shared_paper_count,
    )


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    def list_top_papers(
        self,
        *,
        topic: str | None,
        year: int | None,
        limit: int,
        offset: int,
    ) -> list[AnalyticsPaperItem]:
        papers = self.repository.list_top_papers(
            topic=topic,
            year=year,
            limit=limit,
            offset=offset,
        )
        return [_build_analytics_paper_item(paper) for paper in papers]

    def list_topic_distribution(
        self,
        *,
        year: int | None,
        limit: int,
        offset: int,
    ) -> list[TopicAnalyticsItem]:
        records = self.repository.list_topic_distribution(
            year=year,
            limit=limit,
            offset=offset,
        )
        return [_build_topic_analytics_item(record) for record in records]

    def list_publication_trends(
        self,
        *,
        start_year: int | None,
        end_year: int | None,
    ) -> list[PublicationTrendItem]:
        records = self.repository.list_publication_trends(
            start_year=start_year,
            end_year=end_year,
        )
        return [_build_publication_trend_item(record) for record in records]

    def list_collaboration_pairs(
        self,
        *,
        min_shared_papers: int,
        limit: int,
        offset: int,
    ) -> list[CollaborationPairItem]:
        records = self.repository.list_collaboration_pairs(
            min_shared_papers=min_shared_papers,
            limit=limit,
            offset=offset,
        )
        return [_build_collaboration_pair_item(record) for record in records]
