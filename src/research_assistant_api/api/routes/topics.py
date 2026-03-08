from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from research_assistant_api.db.session import get_db
from research_assistant_api.repositories.topic_repository import TopicRepository
from research_assistant_api.schemas.discovery import PaperSummary, TopicListItem
from research_assistant_api.services import DiscoveryNotFoundError, TopicService

router = APIRouter(prefix="/topics", tags=["topics"])


def _build_service(session: Session) -> TopicService:
    return TopicService(TopicRepository(session))


def _raise_not_found(error: DiscoveryNotFoundError) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
    ) from error


@router.get("", response_model=list[TopicListItem])
def list_topics(
    session: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TopicListItem]:
    service = _build_service(session)
    return service.list_topics(limit=limit, offset=offset)


@router.get("/{topic_id}/papers", response_model=list[PaperSummary])
def list_topic_papers(
    topic_id: str,
    session: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PaperSummary]:
    service = _build_service(session)
    try:
        return service.list_topic_papers(topic_id, limit=limit, offset=offset)
    except DiscoveryNotFoundError as error:
        _raise_not_found(error)
