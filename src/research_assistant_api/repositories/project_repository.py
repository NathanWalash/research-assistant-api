from sqlalchemy import select
from sqlalchemy.orm import Session

from research_assistant_api.models import Project


class ProjectRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, *, user_id: str, title: str, description: str | None) -> Project:
        project = Project(user_id=user_id, title=title, description=description)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def list_for_user(self, user_id: str) -> list[Project]:
        statement = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc(), Project.title.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_for_user(self, project_id: str, user_id: str) -> Project | None:
        statement = select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id,
        )
        return self.session.scalar(statement)

    def save(self, project: Project) -> Project:
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.session.delete(project)
        self.session.commit()
