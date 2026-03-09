from research_assistant_api.models import Annotation, User
from research_assistant_api.repositories.annotation_repository import AnnotationRepository
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.schemas.annotations import (
    AnnotationCreateRequest,
    AnnotationResponse,
    AnnotationUpdateRequest,
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

    def list_annotations(
        self,
        current_user: User,
        paper_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[AnnotationResponse]:
        if not self.paper_repository.exists(paper_id):
            raise DiscoveryNotFoundError("paper", paper_id)

        annotations = self.annotation_repository.list_for_user_and_paper(
            user_id=current_user.id,
            paper_id=paper_id,
            limit=limit,
            offset=offset,
        )
        return [_build_annotation_response(annotation) for annotation in annotations]

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

    def get_annotation(
        self,
        current_user: User,
        annotation_id: str,
    ) -> AnnotationResponse:
        annotation = self.annotation_repository.get_for_user(
            annotation_id,
            current_user.id,
        )
        if annotation is None:
            raise AnnotationNotFoundError(annotation_id)
        return _build_annotation_response(annotation)

    def update_annotation(
        self,
        current_user: User,
        annotation_id: str,
        payload: AnnotationUpdateRequest,
    ) -> AnnotationResponse:
        annotation = self.annotation_repository.get_for_user(
            annotation_id,
            current_user.id,
        )
        if annotation is None:
            raise AnnotationNotFoundError(annotation_id)

        updated_annotation = self.annotation_repository.update(
            annotation,
            text=payload.text.strip(),
        )
        return _build_annotation_response(updated_annotation)

    def delete_annotation(
        self,
        current_user: User,
        annotation_id: str,
    ) -> None:
        annotation = self.annotation_repository.get_for_user(
            annotation_id,
            current_user.id,
        )
        if annotation is None:
            raise AnnotationNotFoundError(annotation_id)
        self.annotation_repository.delete(annotation)


class AnnotationNotFoundError(Exception):
    def __init__(self, annotation_id: str):
        super().__init__(f"annotation '{annotation_id}' was not found")
