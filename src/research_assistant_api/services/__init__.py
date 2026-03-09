"""Service layer helpers for API endpoints."""

from research_assistant_api.services.analytics import AnalyticsService
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

__all__ = [
    "AnalyticsService",
    "AuthenticationError",
    "AuthService",
    "AuthorService",
    "DiscoveryNotFoundError",
    "DuplicateReadingListItemError",
    "PaperService",
    "ProjectNotFoundError",
    "ProjectService",
    "ReadingListItemNotFoundError",
    "ReadingListService",
    "TopicService",
    "UserAlreadyExistsError",
]
