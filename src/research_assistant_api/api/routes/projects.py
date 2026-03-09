from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from research_assistant_api.api.dependencies.auth import get_current_user
from research_assistant_api.db.session import get_db
from research_assistant_api.models import User
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.repositories.project_repository import ProjectRepository
from research_assistant_api.repositories.reading_list_repository import (
    ReadingListRepository,
)
from research_assistant_api.schemas.projects import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from research_assistant_api.schemas.reading_list import (
    ReadingListItemCreateRequest,
    ReadingListItemResponse,
)
from research_assistant_api.services import (
    DiscoveryNotFoundError,
    DuplicateReadingListItemError,
    ProjectNotFoundError,
    ProjectService,
    ReadingListService,
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


def _raise_not_found(error: ProjectNotFoundError) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    ) from error


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    service = _build_service(session)
    return service.create_project(current_user, payload)


@router.get("", response_model=list[ProjectResponse])
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


@router.get("/{project_id}/reading-list", response_model=list[ReadingListItemResponse])
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


@router.get("/{project_id}", response_model=ProjectResponse)
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


@router.patch("/{project_id}", response_model=ProjectResponse)
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


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
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
