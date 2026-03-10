from pydantic import BaseModel

from research_assistant_api.schemas.discovery import TopicSummary


class AnalyticsPaperItem(BaseModel):
    id: str
    title: str
    publication_year: int
    citation_count: int
    journal: str | None = None
    topic: TopicSummary | None = None


class TopicAnalyticsItem(TopicSummary):
    paper_count: int
    total_citation_count: int
    average_citation_count: float


class PublicationTrendItem(BaseModel):
    publication_year: int
    paper_count: int
    total_citation_count: int
    average_citation_count: float
