"""Project use cases."""

from taskapp.errors import NotFoundError
from taskapp.models_generated import Project
from taskapp.services.users import get_user_or_404
from taskapp.services.validation import validate_title
from taskapp.storage.repository import get_repo


def get_project_or_404(store, project_id: int) -> Project:
    project = get_repo(store, "projects").get(project_id)
    if project is None:
        raise NotFoundError(f"project {project_id} not found", code="PROJECT_NOT_FOUND")
    return project


def list_projects(store) -> list[Project]:
    return get_repo(store, "projects").all()


def create_project(store, name, owner_id: int) -> Project:
    get_user_or_404(store, owner_id)
    clean = validate_title(name)
    return get_repo(store, "projects").add(lambda i: Project(id=i, name=clean, owner_id=owner_id))


def archive_project(store, project_id: int) -> Project:
    project = get_project_or_404(store, project_id)
    project.archived = True
    return get_repo(store, "projects").save(project)
