from research_assistant_api.models import Annotation, User
from research_assistant_api.repositories.annotation_repository import AnnotationRepository
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.schemas.annotations import (
    AnnotationCreateRequest,
    AnnotationResponse,
)
from research_assistant_api.services.discovery import DiscoveryNotFoundError


def _build_annotation_response(annotation: Annotation) -> AnnotationResponse:
    return AnnotationResponse(
        id=annotation.id,
        user_id=annotation.user_id,
        paper_id=annotation.paper_id,
        text=annotation.text,
        created_at=annotation.created_at,
    )


class AnnotationService:
    def __init__(
        self,
        annotation_repository: AnnotationRepository,
        paper_repository: PaperRepository,
    ):
        self.annotation_repository = annotation_repository
        self.paper_repository = paper_repository

    def create_annotation(
        self,
        current_user: User,
        paper_id: str,
        payload: AnnotationCreateRequest,
    ) -> AnnotationResponse:
        if not self.paper_repository.exists(paper_id):
            raise DiscoveryNotFoundError("paper", paper_id)

        annotation = self.annotation_repository.create(
            user_id=current_user.id,
            paper_id=paper_id,
            text=payload.text.strip(),
        )
        return _build_annotation_response(annotation)
