from fastapi import FastAPI

from research_assistant_api.api.router import api_router
from research_assistant_api.core.config import get_settings

API_DESCRIPTION = (
    "FastAPI service for scholarly discovery, metadata analytics, semantic "
    "similarity, and user research workflows over the Leeds OpenAlex subset."
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=API_DESCRIPTION,
        debug=settings.debug,
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
