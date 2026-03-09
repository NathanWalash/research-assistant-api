"""Service layer helpers for API endpoints."""

from research_assistant_api.services.analytics import AnalyticsService
from research_assistant_api.services.annotations import AnnotationService
from research_assistant_api.services.auth import (
    AuthenticationError,
    AuthService,
    UserAlreadyExistsError,
)
from research_assistant_api.services.discovery import (
    AuthorService,
    DiscoveryNotFoundError,
    PaperService,
    TopicService,
)
from research_assistant_api.services.projects import ProjectNotFoundError, ProjectService
from research_assistant_api.services.reading_list import (
    DuplicateReadingListItemError,
    ReadingListItemNotFoundError,
    ReadingListService,
)
from research_assistant_api.services.recommendations import (
    ProjectRecommendationsUnavailableError,
    RecommendationService,
)
from research_assistant_api.services.similarity import (
    PaperEmbeddingNotAvailableError,
    SimilarityService,
)

__all__ = [
    "AnalyticsService",
    "AnnotationService",
    "AuthenticationError",
    "AuthService",
    "AuthorService",
    "DiscoveryNotFoundError",
    "DuplicateReadingListItemError",
    "PaperService",
    "ProjectNotFoundError",
    "ProjectRecommendationsUnavailableError",
    "ProjectService",
    "ReadingListItemNotFoundError",
    "ReadingListService",
    "RecommendationService",
    "PaperEmbeddingNotAvailableError",
    "SimilarityService",
    "TopicService",
    "UserAlreadyExistsError",
]
