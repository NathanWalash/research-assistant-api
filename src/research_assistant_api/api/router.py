from fastapi import APIRouter

from research_assistant_api.api.routes.authors import router as authors_router
from research_assistant_api.api.routes.health import router as health_router
from research_assistant_api.api.routes.papers import router as papers_router
from research_assistant_api.api.routes.topics import router as topics_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(papers_router)
api_router.include_router(authors_router)
api_router.include_router(topics_router)


@api_router.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {"service": "research-assistant-api"}
