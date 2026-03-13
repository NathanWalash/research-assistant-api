from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from research_assistant_api.api.dependencies.auth import get_current_user
from research_assistant_api.api.openapi_responses import (
    RESPONSE_401_UNAUTHORIZED,
    RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
    RESPONSE_422_VALIDATION,
    merge_responses,
)
from research_assistant_api.db.session import get_db
from research_assistant_api.models import User
from research_assistant_api.repositories.annotation_repository import AnnotationRepository
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.schemas.annotations import (
    AnnotationResponse,
    AnnotationUpdateRequest,
)
from research_assistant_api.services import AnnotationNotFoundError, AnnotationService

router = APIRouter(prefix="/annotations", tags=["annotations"])


def _build_service(session: Session) -> AnnotationService:
    return AnnotationService(
        annotation_repository=AnnotationRepository(session),
        paper_repository=PaperRepository(session),
    )


def _raise_not_found(error: AnnotationNotFoundError) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    ) from error


@router.get(
    "/{annotation_id}",
    response_model=AnnotationResponse,
    summary="Get annotation",
    description="Fetch a single private annotation owned by the authenticated user.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_422_VALIDATION,
    ),
)
def get_annotation(
    annotation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> AnnotationResponse:
    service = _build_service(session)
    try:
        return service.get_annotation(current_user, annotation_id)
    except AnnotationNotFoundError as error:
        _raise_not_found(error)


@router.patch(
    "/{annotation_id}",
    response_model=AnnotationResponse,
    summary="Update annotation",
    description="Update the text of a private annotation owned by the authenticated user.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_422_VALIDATION,
    ),
)
def update_annotation(
    annotation_id: str,
    payload: AnnotationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> AnnotationResponse:
    service = _build_service(session)
    try:
        return service.update_annotation(current_user, annotation_id, payload)
    except AnnotationNotFoundError as error:
        _raise_not_found(error)


@router.delete(
    "/{annotation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete annotation",
    description="Delete a private annotation owned by the authenticated user.",
    responses=merge_responses(
        RESPONSE_401_UNAUTHORIZED,
        RESPONSE_404_NOT_FOUND_OR_NOT_OWNED,
        RESPONSE_422_VALIDATION,
    ),
)
def delete_annotation(
    annotation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    service = _build_service(session)
    try:
        service.delete_annotation(current_user, annotation_id)
    except AnnotationNotFoundError as error:
        _raise_not_found(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
