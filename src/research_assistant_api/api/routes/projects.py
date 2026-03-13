from typing import Annotated
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from research_assistant_api.api.dependencies.auth import get_current_user
from research_assistant_api.api.openapi_responses import (
    RESPONSE_401_UNAUTHORIZED,
    RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
    RESPONSE_409_CONFLICT,
    RESPONSE_422_VALIDATION,
    merge_responses,
)
from research_assistant_api.db.session import get_db
from research_assistant_api.models import User
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.repositories.project_repository import ProjectRepository
from research_assistant_api.repositories.reading_list_repository import (
    ReadingListRepository,
)
from research_assistant_api.repositories.citation_repository import CitationRepository
from research_assistant_api.repositories.similarity_repository import SimilarityRepository
from research_assistant_api.schemas.projects import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from research_assistant_api.schemas.recommendations import (
    ProjectRecommendationResponse,
)
from research_assistant_api.schemas.reading_list import (
    ReadingListItemCreateRequest,
    ReadingListItemResponse,
)
from research_assistant_api.services import (
    DiscoveryNotFoundError,
    DuplicateReadingListItemError,
    ProjectNotFoundError,
    ProjectRecommendationsUnavailableError,
    ProjectService,
    ReadingListService,
    RecommendationService,
    InvalidRecommendationWeightsError,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _build_service(session: Session) -> ProjectService:
    return ProjectService(ProjectRepository(session))


def _build_reading_list_service(session: Session) -> ReadingListService:
    return ReadingListService(
        project_repository=ProjectRepository(session),
        reading_list_repository=ReadingListRepository(session),
        paper_repository=PaperRepository(session),
    )


def _build_recommendation_service(session: Session) -> RecommendationService:
    return RecommendationService(
        project_repository=ProjectRepository(session),
        reading_list_repository=ReadingListRepository(session),
        similarity_repository=SimilarityRepository(session),
        citation_repository=CitationRepository(session),
    )


def _raise_not_found(error: ProjectNotFoundError) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    ) from error


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Create a user-owned research project.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_422_VALIDATION,
    ),
)
def create_project(
    payload: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    service = _build_service(session)
    return service.create_project(current_user, payload)


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List projects",
    description="List projects owned by the authenticated user.",
    responses=RESPONSE_401_UNAUTHORIZED,
)
def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[ProjectResponse]:
    service = _build_service(session)
    return service.list_projects(current_user)


@router.post(
    "/{project_id}/reading-list",
    response_model=ReadingListItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add reading-list item",
    description="Add a paper to a project reading list.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_409_CONFLICT,
        RESPONSE_422_VALIDATION,
    ),
)
def add_reading_list_item(
    project_id: str,
    payload: ReadingListItemCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ReadingListItemResponse:
    service = _build_reading_list_service(session)
    try:
        return service.add_item(current_user, project_id, payload)
    except (ProjectNotFoundError, DiscoveryNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except DuplicateReadingListItemError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/{project_id}/reading-list",
    response_model=list[ReadingListItemResponse],
    summary="List reading-list items",
    description="List reading-list items for a user-owned project.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_422_VALIDATION,
    ),
)
def list_reading_list_items(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[ReadingListItemResponse]:
    service = _build_reading_list_service(session)
    try:
        return service.list_items(current_user, project_id)
    except ProjectNotFoundError as error:
        _raise_not_found(error)


@router.get(
    "/{project_id}/recommendations",
    response_model=list[ProjectRecommendationResponse],
    summary="List project recommendations",
    description="Recommend papers from reading-list context using semantic, citation, or hybrid scoring.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_409_CONFLICT,
        RESPONSE_422_VALIDATION,
    ),
)
def list_project_recommendations(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    scoring_mode: Annotated[
        Literal["semantic", "citation", "hybrid"],
        Query(alias="mode"),
    ] = "hybrid",
    semantic_weight: Annotated[float | None, Query(ge=0, le=1)] = None,
    citation_weight: Annotated[float | None, Query(ge=0, le=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProjectRecommendationResponse]:
    service = _build_recommendation_service(session)
    try:
        return service.list_project_recommendations(
            current_user,
            project_id,
            scoring_mode=scoring_mode,
            semantic_weight=semantic_weight,
            citation_weight=citation_weight,
            limit=limit,
            offset=offset,
        )
    except ProjectNotFoundError as error:
        _raise_not_found(error)
    except ProjectRecommendationsUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except InvalidRecommendationWeightsError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project",
    description="Return a single project owned by the authenticated user.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_422_VALIDATION,
    ),
)
def get_project(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    service = _build_service(session)
    try:
        return service.get_project(current_user, project_id)
    except ProjectNotFoundError as error:
        _raise_not_found(error)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update the title or description of a user-owned project.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_422_VALIDATION,
    ),
)
def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    service = _build_service(session)
    try:
        return service.update_project(current_user, project_id, payload)
    except ProjectNotFoundError as error:
        _raise_not_found(error)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a user-owned project and its dependent workflow records.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_422_VALIDATION,
    ),
)
def delete_project(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    service = _build_service(session)
    try:
        service.delete_project(current_user, project_id)
    except ProjectNotFoundError as error:
        _raise_not_found(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
