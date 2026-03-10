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


@router.get(
    "",
    response_model=list[AuthorDetail],
    summary="List authors",
    description="List authors in the local Leeds corpus subset.",
)
def list_authors(
    session: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuthorDetail]:
    service = _build_service(session)
    return service.list_authors(
        query=None,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/search",
    response_model=list[AuthorDetail],
    summary="Search authors",
    description="Search authors in the local Leeds corpus subset by name or author id.",
)
def search_authors(
    session: Annotated[Session, Depends(get_db)],
    query: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuthorDetail]:
    service = _build_service(session)
    return service.list_authors(
        query=query,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{author_id:path}/papers",
    response_model=list[PaperSummary],
    summary="List author papers",
    description="List papers associated with a specific author id.",
)
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


@router.get(
    "/{author_id:path}",
    response_model=AuthorDetail,
    summary="Get author",
    description="Return author metadata and affiliation details.",
)
def get_author(
    author_id: str, session: Annotated[Session, Depends(get_db)]
) -> AuthorDetail:
    service = _build_service(session)
    try:
        return service.get_author(author_id)
    except DiscoveryNotFoundError as error:
        _raise_not_found(error)
