"""Pydantic schemas for API responses and requests."""

from research_assistant_api.schemas.analytics import (
    AnalyticsPaperItem,
    CollaborationPairItem,
    PublicationTrendItem,
    TopicAnalyticsItem,
)
from research_assistant_api.schemas.annotations import (
    AnnotationCreateRequest,
    AnnotationResponse,
    AnnotationUpdateRequest,
)
from research_assistant_api.schemas.auth import (
    AccessTokenResponse,
    AuthenticatedUser,
    UserLoginRequest,
    UserRegistrationRequest,
)
from research_assistant_api.schemas.citations import (
    CitationNeighborhoodResponse,
    CitationPathResponse,
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
from research_assistant_api.schemas.projects import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from research_assistant_api.schemas.reading_list import (
    ReadingListItemCreateRequest,
    ReadingListItemResponse,
    ReadingListItemUpdateRequest,
)
from research_assistant_api.schemas.recommendations import (
    ProjectRecommendationResponse,
)
from research_assistant_api.schemas.similarity import SimilarPaperResponse

__all__ = [
    "AnalyticsPaperItem",
    "AccessTokenResponse",
    "AuthorDetail",
    "AnnotationCreateRequest",
    "AnnotationResponse",
    "AnnotationUpdateRequest",
    "AuthenticatedUser",
    "CitationNeighborhoodResponse",
    "CitationPathResponse",
    "CollaborationPairItem",
    "InstitutionSummary",
    "PaperAuthorSummary",
    "PaperDetail",
    "PaperSummary",
    "PublicationTrendItem",
    "ProjectCreateRequest",
    "ProjectRecommendationResponse",
    "ProjectResponse",
    "ProjectUpdateRequest",
    "ReadingListItemCreateRequest",
    "ReadingListItemResponse",
    "ReadingListItemUpdateRequest",
    "SimilarPaperResponse",
    "TopicAnalyticsItem",
    "TopicListItem",
    "TopicSummary",
    "UserLoginRequest",
    "UserRegistrationRequest",
]
