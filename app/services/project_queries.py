from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectRead
from app.cache.project import ProjectCache


class ProjectQueryService:
    def __init__(self, project_repo: ProjectRepository, project_cache: ProjectCache):

        self.project_repo = project_repo
        self.project_cache = project_cache

    def list_accessible_by_user(self, user_id: int) -> list[ProjectRead]:

        cached_projects = self.project_cache.get_user_projects(user_id)

        if cached_projects is not None:
            return cached_projects

        projects = self.project_repo.list_accessible_by_user(user_id)

        project_reads = [
            ProjectRead.model_validate(project, from_attributes=True)
            for project in projects
        ]

        self.project_cache.set_user_projects(user_id, project_reads)

        return project_reads
