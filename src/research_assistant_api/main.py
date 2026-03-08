from fastapi import FastAPI

from research_assistant_api.api.router import api_router
from research_assistant_api.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
