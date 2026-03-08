from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from research_assistant_api.db.session import get_db
from research_assistant_api.repositories.author_repository import AuthorRepository
from research_assistant_api.schemas.discovery import AuthorDetail, PaperSummary
from research_assistant_api.services import AuthorService, DiscoveryNotFoundError

router = APIRouter(prefix="/authors", tags=["authors"])


def _build_service(session: Session) -> AuthorService:
    return AuthorService(AuthorRepository(session))


def _raise_not_found(error: DiscoveryNotFoundError) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
    ) from error


@router.get("/{author_id:path}/papers", response_model=list[PaperSummary])
def list_author_papers(
    author_id: str,
    session: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PaperSummary]:
    service = _build_service(session)
    try:
        return service.list_author_papers(author_id, limit=limit, offset=offset)
    except DiscoveryNotFoundError as error:
        _raise_not_found(error)


@router.get("/{author_id:path}", response_model=AuthorDetail)
def get_author(
    author_id: str, session: Annotated[Session, Depends(get_db)]
) -> AuthorDetail:
    service = _build_service(session)
    try:
        return service.get_author(author_id)
    except DiscoveryNotFoundError as error:
        _raise_not_found(error)
