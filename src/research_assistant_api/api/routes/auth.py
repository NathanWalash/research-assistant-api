from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from research_assistant_api.db.session import get_db
from research_assistant_api.repositories.user_repository import UserRepository
from research_assistant_api.schemas.auth import (
    AccessTokenResponse,
    UserLoginRequest,
    UserRegistrationRequest,
)
from research_assistant_api.services import (
    AuthenticationError,
    AuthService,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_service(session: Session) -> AuthService:
    return AuthService(UserRepository(session))


@router.post(
    "/register",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegistrationRequest,
    session: Annotated[Session, Depends(get_db)],
) -> AccessTokenResponse:
    service = _build_service(session)
    try:
        return service.register(payload)
    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post("/login", response_model=AccessTokenResponse)
def login(
    payload: UserLoginRequest,
    session: Annotated[Session, Depends(get_db)],
) -> AccessTokenResponse:
    service = _build_service(session)
    try:
        return service.login(payload)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error
