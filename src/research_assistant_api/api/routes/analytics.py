from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from research_assistant_api.db.session import get_db
from research_assistant_api.repositories.analytics_repository import AnalyticsRepository
from research_assistant_api.schemas.analytics import (
    AnalyticsPaperItem,
    CollaborationPairItem,
    PublicationTrendItem,
    TopicAnalyticsItem,
)
from research_assistant_api.services import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _build_service(session: Session) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(session))


@router.get("/top-papers", response_model=list[AnalyticsPaperItem])
def list_top_papers(
    session: Annotated[Session, Depends(get_db)],
    topic: str | None = None,
    year: int | None = Query(default=None, ge=0),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AnalyticsPaperItem]:
    service = _build_service(session)
    return service.list_top_papers(
        topic=topic,
        year=year,
        limit=limit,
        offset=offset,
    )


@router.get("/topics", response_model=list[TopicAnalyticsItem])
def list_topic_distribution(
    session: Annotated[Session, Depends(get_db)],
    year: int | None = Query(default=None, ge=0),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TopicAnalyticsItem]:
    service = _build_service(session)
    return service.list_topic_distribution(
        year=year,
        limit=limit,
        offset=offset,
    )


@router.get("/trends", response_model=list[PublicationTrendItem])
def list_publication_trends(
    session: Annotated[Session, Depends(get_db)],
    start_year: int | None = Query(default=None, ge=0),
    end_year: int | None = Query(default=None, ge=0),
) -> list[PublicationTrendItem]:
    service = _build_service(session)
    return service.list_publication_trends(
        start_year=start_year,
        end_year=end_year,
    )


@router.get("/collaborations", response_model=list[CollaborationPairItem])
def list_collaboration_pairs(
    session: Annotated[Session, Depends(get_db)],
    min_shared_papers: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CollaborationPairItem]:
    service = _build_service(session)
    return service.list_collaboration_pairs(
        min_shared_papers=min_shared_papers,
        limit=limit,
        offset=offset,
    )
