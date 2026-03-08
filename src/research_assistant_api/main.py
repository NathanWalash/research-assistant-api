from fastapi import FastAPI

from research_assistant_api.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Research Assistant API")
    app.include_router(api_router)
    return app


app = create_app()
