from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {"service": "research-assistant-api"}
