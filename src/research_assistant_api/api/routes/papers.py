from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from research_assistant_api.db.session import get_db
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.schemas.discovery import PaperDetail, PaperSummary
from research_assistant_api.services import DiscoveryNotFoundError, PaperService

router = APIRouter(prefix="/papers", tags=["papers"])


def _build_service(session: Session) -> PaperService:
    return PaperService(PaperRepository(session))


def _raise_not_found(error: DiscoveryNotFoundError) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
    ) from error


@router.get("/search", response_model=list[PaperSummary])
def search_papers(
    session: Annotated[Session, Depends(get_db)],
    query: str | None = None,
    topic: str | None = None,
    year: int | None = Query(default=None, ge=0),
    citation_count: int | None = Query(default=None, ge=0),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PaperSummary]:
    service = _build_service(session)
    return service.search_papers(
        query=query,
        topic=topic,
        year=year,
        citation_count=citation_count,
        limit=limit,
        offset=offset,
    )


@router.get("/{paper_id:path}", response_model=PaperDetail)
def get_paper(
    paper_id: str, session: Annotated[Session, Depends(get_db)]
) -> PaperDetail:
    service = _build_service(session)
    try:
        return service.get_paper(paper_id)
    except DiscoveryNotFoundError as error:
        _raise_not_found(error)
