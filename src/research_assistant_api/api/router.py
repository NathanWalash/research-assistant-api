from fastapi import APIRouter

from research_assistant_api.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)


@api_router.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {"service": "research-assistant-api"}
