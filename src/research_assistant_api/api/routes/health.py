from fastapi import APIRouter

from research_assistant_api.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Return a lightweight liveness response for the API service.",
)
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }
