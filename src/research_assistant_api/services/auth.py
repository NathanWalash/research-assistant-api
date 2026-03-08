from research_assistant_api.core import (
    create_access_token,
    hash_password,
    verify_password,
)
from research_assistant_api.models import User
from research_assistant_api.repositories.user_repository import UserRepository
from research_assistant_api.schemas.auth import (
    AccessTokenResponse,
    AuthenticatedUser,
    UserLoginRequest,
    UserRegistrationRequest,
)


class AuthenticationError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _build_authenticated_user(user: User) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
    )


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(self, payload: UserRegistrationRequest) -> AccessTokenResponse:
        normalized_email = _normalize_email(payload.email)
        existing_user = self.repository.get_by_email(normalized_email)
        if existing_user is not None:
            raise UserAlreadyExistsError(
                f"user with email '{normalized_email}' already exists"
            )

        user = self.repository.create(
            email=normalized_email,
            password_hash=hash_password(payload.password),
        )
        return AccessTokenResponse(
            access_token=create_access_token(user.id),
            user=_build_authenticated_user(user),
        )

    def login(self, payload: UserLoginRequest) -> AccessTokenResponse:
        normalized_email = _normalize_email(payload.email)
        user = self.repository.get_by_email(normalized_email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise AuthenticationError("invalid email or password")

        return AccessTokenResponse(
            access_token=create_access_token(user.id),
            user=_build_authenticated_user(user),
        )
