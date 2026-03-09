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
from research_assistant_api.schemas.reading_list import (
    ReadingListItemCreateRequest,
    ReadingListItemResponse,
    ReadingListItemUpdateRequest,
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
    "ReadingListItemCreateRequest",
    "ReadingListItemResponse",
    "ReadingListItemUpdateRequest",
    "TopicAnalyticsItem",
    "TopicListItem",
    "TopicSummary",
    "UserLoginRequest",
    "UserRegistrationRequest",
]
