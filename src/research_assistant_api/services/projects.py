from research_assistant_api.models import Project, User
from research_assistant_api.repositories.project_repository import ProjectRepository
from research_assistant_api.schemas.projects import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)


class ProjectNotFoundError(Exception):
    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"project '{project_id}' was not found")


def _build_project_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        description=project.description,
        created_at=project.created_at,
    )


class ProjectService:
    def __init__(self, repository: ProjectRepository):
        self.repository = repository

    def create_project(
        self,
        current_user: User,
        payload: ProjectCreateRequest,
    ) -> ProjectResponse:
        project = self.repository.create(
            user_id=current_user.id,
            title=payload.title.strip(),
            description=payload.description,
        )
        return _build_project_response(project)

    def list_projects(self, current_user: User) -> list[ProjectResponse]:
        projects = self.repository.list_for_user(current_user.id)
        return [_build_project_response(project) for project in projects]

    def get_project(self, current_user: User, project_id: str) -> ProjectResponse:
        project = self.repository.get_for_user(project_id, current_user.id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return _build_project_response(project)

    def update_project(
        self,
        current_user: User,
        project_id: str,
        payload: ProjectUpdateRequest,
    ) -> ProjectResponse:
        project = self.repository.get_for_user(project_id, current_user.id)
        if project is None:
            raise ProjectNotFoundError(project_id)

        if payload.title is not None:
            project.title = payload.title.strip()
        if payload.description is not None:
            project.description = payload.description

        return _build_project_response(self.repository.save(project))

    def delete_project(self, current_user: User, project_id: str) -> None:
        project = self.repository.get_for_user(project_id, current_user.id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        self.repository.delete(project)
