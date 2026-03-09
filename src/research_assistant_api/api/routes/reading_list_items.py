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
from research_assistant_api.schemas.reading_list import (
    ReadingListItemResponse,
    ReadingListItemUpdateRequest,
)
from research_assistant_api.services import (
    ReadingListItemNotFoundError,
    ReadingListService,
)

router = APIRouter(prefix="/reading-list-items", tags=["reading-list"])


def _build_service(session: Session) -> ReadingListService:
    return ReadingListService(
        project_repository=ProjectRepository(session),
        reading_list_repository=ReadingListRepository(session),
        paper_repository=PaperRepository(session),
    )


def _raise_not_found(error: ReadingListItemNotFoundError) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    ) from error


@router.patch(
    "/{item_id}",
    response_model=ReadingListItemResponse,
    summary="Update reading-list item",
    description="Update reading-list priority or notes for an item owned by the authenticated user.",
)
def update_reading_list_item(
    item_id: str,
    payload: ReadingListItemUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ReadingListItemResponse:
    service = _build_service(session)
    try:
        return service.update_item(current_user, item_id, payload)
    except ReadingListItemNotFoundError as error:
        _raise_not_found(error)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete reading-list item",
    description="Delete a reading-list item owned by the authenticated user.",
)
def delete_reading_list_item(
    item_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    service = _build_service(session)
    try:
        service.delete_item(current_user, item_id)
    except ReadingListItemNotFoundError as error:
        _raise_not_found(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
