from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from research_assistant_api.models import Paper, Project, ReadingListItem


class ReadingListRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        project_id: str,
        paper_id: str,
        priority: str,
        notes: str | None,
    ) -> ReadingListItem:
        item = ReadingListItem(
            project_id=project_id,
            paper_id=paper_id,
            priority=priority,
            notes=notes,
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return self.get_for_user(item.id, self._get_project_owner(project_id)) or item

    def list_for_project(self, project_id: str) -> list[ReadingListItem]:
        statement = (
            select(ReadingListItem)
            .options(selectinload(ReadingListItem.paper).selectinload(Paper.topic))
            .where(ReadingListItem.project_id == project_id)
            .order_by(ReadingListItem.created_at.desc(), ReadingListItem.id.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_for_project_and_paper(
        self,
        project_id: str,
        paper_id: str,
    ) -> ReadingListItem | None:
        statement = select(ReadingListItem).where(
            ReadingListItem.project_id == project_id,
            ReadingListItem.paper_id == paper_id,
        )
        return self.session.scalar(statement)

    def get_for_user(self, item_id: str, user_id: str) -> ReadingListItem | None:
        statement = (
            select(ReadingListItem)
            .join(Project, Project.id == ReadingListItem.project_id)
            .options(selectinload(ReadingListItem.paper).selectinload(Paper.topic))
            .where(
                ReadingListItem.id == item_id,
                Project.user_id == user_id,
            )
        )
        return self.session.scalar(statement)

    def save(self, item: ReadingListItem) -> ReadingListItem:
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return self.get_for_user(item.id, self._get_project_owner(item.project_id)) or item

    def delete(self, item: ReadingListItem) -> None:
        self.session.delete(item)
        self.session.commit()

    def _get_project_owner(self, project_id: str) -> str:
        statement = select(Project.user_id).where(Project.id == project_id)
        owner_id = self.session.scalar(statement)
        if owner_id is None:
            raise ValueError("project owner could not be resolved")
        return owner_id
