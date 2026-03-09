from research_assistant_api.models import Paper, ReadingListItem, User
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.repositories.project_repository import ProjectRepository
from research_assistant_api.repositories.reading_list_repository import (
    ReadingListRepository,
)
from research_assistant_api.schemas.discovery import PaperSummary, TopicSummary
from research_assistant_api.schemas.reading_list import (
    ReadingListItemCreateRequest,
    ReadingListItemResponse,
    ReadingListItemUpdateRequest,
)
from research_assistant_api.services.discovery import DiscoveryNotFoundError
from research_assistant_api.services.projects import ProjectNotFoundError


class DuplicateReadingListItemError(Exception):
    def __init__(self, paper_id: str):
        self.paper_id = paper_id
        super().__init__(f"paper '{paper_id}' is already in the reading list")


class ReadingListItemNotFoundError(Exception):
    def __init__(self, item_id: str):
        self.item_id = item_id
        super().__init__(f"reading list item '{item_id}' was not found")


def _build_topic_summary(topic: object | None) -> TopicSummary | None:
    if topic is None:
        return None
    return TopicSummary.model_validate(topic)


def _build_paper_summary(paper: Paper) -> PaperSummary:
    return PaperSummary(
        id=paper.id,
        title=paper.title,
        publication_year=paper.publication_year,
        publication_date=paper.publication_date,
        citation_count=paper.citation_count,
        doi=paper.doi,
        journal=paper.journal,
        language=paper.language,
        work_type=paper.work_type,
        topic=_build_topic_summary(paper.topic),
    )


def _build_item_response(item: ReadingListItem) -> ReadingListItemResponse:
    return ReadingListItemResponse(
        id=item.id,
        project_id=item.project_id,
        paper_id=item.paper_id,
        priority=item.priority,
        notes=item.notes,
        created_at=item.created_at,
        paper=_build_paper_summary(item.paper),
    )


class ReadingListService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        reading_list_repository: ReadingListRepository,
        paper_repository: PaperRepository,
    ):
        self.project_repository = project_repository
        self.reading_list_repository = reading_list_repository
        self.paper_repository = paper_repository

    def add_item(
        self,
        current_user: User,
        project_id: str,
        payload: ReadingListItemCreateRequest,
    ) -> ReadingListItemResponse:
        project = self.project_repository.get_for_user(project_id, current_user.id)
        if project is None:
            raise ProjectNotFoundError(project_id)

        if not self.paper_repository.exists(payload.paper_id):
            raise DiscoveryNotFoundError("paper", payload.paper_id)

        if (
            self.reading_list_repository.get_for_project_and_paper(
                project_id,
                payload.paper_id,
            )
            is not None
        ):
            raise DuplicateReadingListItemError(payload.paper_id)

        item = self.reading_list_repository.create(
            project_id=project_id,
            paper_id=payload.paper_id,
            priority=payload.priority,
            notes=payload.notes,
        )
        return _build_item_response(item)

    def list_items(
        self,
        current_user: User,
        project_id: str,
    ) -> list[ReadingListItemResponse]:
        project = self.project_repository.get_for_user(project_id, current_user.id)
        if project is None:
            raise ProjectNotFoundError(project_id)

        items = self.reading_list_repository.list_for_project(project_id)
        return [_build_item_response(item) for item in items]

    def update_item(
        self,
        current_user: User,
        item_id: str,
        payload: ReadingListItemUpdateRequest,
    ) -> ReadingListItemResponse:
        item = self.reading_list_repository.get_for_user(item_id, current_user.id)
        if item is None:
            raise ReadingListItemNotFoundError(item_id)

        if "priority" in payload.model_fields_set and payload.priority is not None:
            item.priority = payload.priority
        if "notes" in payload.model_fields_set:
            item.notes = payload.notes

        return _build_item_response(self.reading_list_repository.save(item))

    def delete_item(self, current_user: User, item_id: str) -> None:
        item = self.reading_list_repository.get_for_user(item_id, current_user.id)
        if item is None:
            raise ReadingListItemNotFoundError(item_id)
        self.reading_list_repository.delete(item)
