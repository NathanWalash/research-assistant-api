"""Pydantic schemas for API responses and requests."""

from research_assistant_api.schemas.analytics import (
    AnalyticsPaperItem,
    CollaborationPairItem,
    PublicationTrendItem,
    TopicAnalyticsItem,
)
from research_assistant_api.schemas.discovery import (
    AuthorDetail,
    InstitutionSummary,
    PaperAuthorSummary,
    PaperDetail,
    PaperSummary,
    TopicListItem,
    TopicSummary,
)

__all__ = [
    "AnalyticsPaperItem",
    "AuthorDetail",
    "CollaborationPairItem",
    "InstitutionSummary",
    "PaperAuthorSummary",
    "PaperDetail",
    "PaperSummary",
    "PublicationTrendItem",
    "TopicAnalyticsItem",
    "TopicListItem",
    "TopicSummary",
]
