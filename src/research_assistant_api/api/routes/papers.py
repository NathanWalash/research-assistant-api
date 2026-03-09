from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from research_assistant_api.api.dependencies.auth import get_current_user
from research_assistant_api.db.session import get_db
from research_assistant_api.models import User
from research_assistant_api.repositories.annotation_repository import AnnotationRepository
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.repositories.similarity_repository import SimilarityRepository
from research_assistant_api.schemas.annotations import (
    AnnotationCreateRequest,
    AnnotationResponse,
)
from research_assistant_api.schemas.discovery import PaperDetail, PaperSummary
from research_assistant_api.schemas.similarity import SimilarPaperResponse
from research_assistant_api.services import (
    AnnotationService,
    DiscoveryNotFoundError,
    PaperService,
    PaperEmbeddingNotAvailableError,
    SimilarityService,
)

router = APIRouter(prefix="/papers", tags=["papers"])


def _build_service(session: Session) -> PaperService:
    return PaperService(PaperRepository(session))


def _build_annotation_service(session: Session) -> AnnotationService:
    return AnnotationService(
        annotation_repository=AnnotationRepository(session),
        paper_repository=PaperRepository(session),
    )


def _build_similarity_service(session: Session) -> SimilarityService:
    return SimilarityService(SimilarityRepository(session))


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


@router.post(
    "/{paper_id:path}/annotations",
    response_model=AnnotationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_annotation(
    paper_id: str,
    payload: AnnotationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> AnnotationResponse:
    service = _build_annotation_service(session)
    try:
        return service.create_annotation(current_user, paper_id, payload)
    except DiscoveryNotFoundError as error:
        _raise_not_found(error)


@router.get("/{paper_id:path}/similar", response_model=list[SimilarPaperResponse])
def list_similar_papers(
    paper_id: str,
    session: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SimilarPaperResponse]:
    service = _build_similarity_service(session)
    try:
        return service.list_similar_papers(
            paper_id,
            limit=limit,
            offset=offset,
        )
    except DiscoveryNotFoundError as error:
        _raise_not_found(error)
    except PaperEmbeddingNotAvailableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get("/{paper_id:path}", response_model=PaperDetail)
def get_paper(
    paper_id: str, session: Annotated[Session, Depends(get_db)]
) -> PaperDetail:
    service = _build_service(session)
    try:
        return service.get_paper(paper_id)
    except DiscoveryNotFoundError as error:
        _raise_not_found(error)
