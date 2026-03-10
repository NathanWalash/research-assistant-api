from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from research_assistant_api.api.router import api_router
from research_assistant_api.core.config import get_settings

API_DESCRIPTION = (
    "FastAPI service for scholarly discovery, metadata analytics, semantic "
    "similarity, and user research workflows over the Leeds OpenAlex subset."
)
OPENAPI_TAGS = [
    {"name": "health", "description": "Service health and liveness endpoints."},
    {"name": "auth", "description": "User registration, login, and bearer-token identity."},
    {"name": "analytics", "description": "Corpus-level analytics, top-paper ranking, and publication trends."},
    {"name": "papers", "description": "Paper discovery, detail, similarity, citations, and paper-scoped annotations."},
    {"name": "annotations", "description": "Private annotation read, update, and delete operations."},
    {"name": "projects", "description": "User-owned projects, reading lists, and recommendation workflows."},
    {"name": "reading-list", "description": "Reading-list item update and delete operations."},
    {"name": "authors", "description": "Author search, detail, and paper lookup endpoints."},
    {"name": "topics", "description": "Topic lookup and topic-scoped paper listing."},
]


def _frontend_directory() -> Path:
    return Path(__file__).resolve().parent / "frontend"


def create_app() -> FastAPI:
    settings = get_settings()
    frontend_dir = _frontend_directory()
    frontend_pages = {
        "": "index.html",
        "login": "login.html",
        "register": "register.html",
        "discover": "discover.html",
        "endpoints": "endpoints.html",
        "projects": "projects.html",
        "analytics": "analytics.html",
        "account": "account.html",
    }
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        debug=settings.debug,
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    app.mount(
        "/app/static",
        StaticFiles(directory=str(frontend_dir)),
        name="frontend-static",
    )

    @app.get("/app", include_in_schema=False)
    @app.get("/app/", include_in_schema=False)
    def serve_frontend_index() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    @app.get("/app/{page_name}", include_in_schema=False)
    def serve_frontend_page(page_name: str) -> FileResponse:
        filename = frontend_pages.get(page_name)
        if filename is None:
            raise HTTPException(status_code=404, detail="frontend page was not found")
        return FileResponse(frontend_dir / filename)

    return app


app = create_app()
