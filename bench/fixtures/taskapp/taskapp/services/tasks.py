"""Task use cases."""

from taskapp.constants import DEFAULT_PAGE_SIZE, DEFAULT_PRIORITY
from taskapp.errors import ConflictError, NotFoundError
from taskapp.models_generated import Task
from taskapp.services.pagination import Page, paginate
from taskapp.services.projects import get_project_or_404
from taskapp.services.validation import validate_priority, validate_status, validate_title
from taskapp.storage.repository import get_repo


def get_task_or_404(store, task_id: int) -> Task:
    task = get_repo(store, "tasks").get(task_id)
    if task is None:
        raise NotFoundError(f"task {task_id} not found", code="TASK_NOT_FOUND")
    return task


def tasks_for_project(store, project_id: int) -> list[Task]:
    get_project_or_404(store, project_id)
    return [task for task in get_repo(store, "tasks").all() if task.project_id == project_id]


def create_task(store, project_id: int, title, priority=DEFAULT_PRIORITY) -> Task:
    project = get_project_or_404(store, project_id)
    if project.archived:
        raise ConflictError("project is archived", code="PROJECT_ARCHIVED")
    clean_title = validate_title(title)
    clean_priority = validate_priority(priority)
    return get_repo(store, "tasks").add(
        lambda i: Task(id=i, project_id=project_id, title=clean_title, priority=clean_priority)
    )


def update_task(store, task_id: int, changes: dict) -> Task:
    task = get_task_or_404(store, task_id)
    if "title" in changes:
        task.title = validate_title(changes["title"])
    if "status" in changes:
        task.status = validate_status(changes["status"])
    if "priority" in changes:
        task.priority = validate_priority(changes["priority"])
    return get_repo(store, "tasks").save(task)


def search_tasks(store, query: str, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
    needle = query.strip().lower()
    matches = [task for task in get_repo(store, "tasks").all() if needle in task.title.lower()]
    return paginate(matches, page=page, page_size=page_size)
