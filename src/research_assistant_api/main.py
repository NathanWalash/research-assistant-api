from fastapi import FastAPI

from research_assistant_api.api.router import api_router
from research_assistant_api.core.config import get_settings

API_DESCRIPTION = (
    "FastAPI service for scholarly discovery, metadata analytics, semantic "
    "similarity, and user research workflows over the Leeds OpenAlex subset."
)
OPENAPI_TAGS = [
    {"name": "health", "description": "Service health and liveness endpoints."},
    {"name": "meta", "description": "Root service metadata."},
    {"name": "auth", "description": "User registration, login, and bearer-token identity."},
    {"name": "analytics", "description": "Corpus-level analytics, trends, and collaboration summaries."},
    {"name": "papers", "description": "Paper discovery, detail, similarity, citations, and paper-scoped annotations."},
    {"name": "annotations", "description": "Private annotation read, update, and delete operations."},
    {"name": "projects", "description": "User-owned projects, reading lists, and recommendation workflows."},
    {"name": "reading-list", "description": "Reading-list item update and delete operations."},
    {"name": "authors", "description": "Author detail and paper lookup endpoints."},
    {"name": "topics", "description": "Topic lookup and topic-scoped paper listing."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        debug=settings.debug,
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
