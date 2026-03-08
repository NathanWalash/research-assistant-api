"""Pydantic schemas for API responses and requests."""

from research_assistant_api.schemas.analytics import (
    AnalyticsPaperItem,
    CollaborationPairItem,
    PublicationTrendItem,
    TopicAnalyticsItem,
)
from research_assistant_api.schemas.auth import (
    AccessTokenResponse,
    AuthenticatedUser,
    UserLoginRequest,
    UserRegistrationRequest,
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

__all__ = [
    "AnalyticsPaperItem",
    "AccessTokenResponse",
    "AuthorDetail",
    "AuthenticatedUser",
    "CollaborationPairItem",
    "InstitutionSummary",
    "PaperAuthorSummary",
    "PaperDetail",
    "PaperSummary",
    "PublicationTrendItem",
    "ProjectCreateRequest",
    "ProjectResponse",
    "ProjectUpdateRequest",
    "TopicAnalyticsItem",
    "TopicListItem",
    "TopicSummary",
    "UserLoginRequest",
    "UserRegistrationRequest",
]
