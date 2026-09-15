"""Task routes."""

from taskapp.constants import DEFAULT_PAGE_SIZE, DEFAULT_PRIORITY, HTTP_CREATED, HTTP_OK
from taskapp.services import tasks as task_service
from taskapp.services.pagination import paginate
from taskapp.utils.ids import parse_id
from taskapp.utils.querystring import parse_page_params


def list_tasks(store, request, project_id):
    page, size = parse_page_params(request.query, default_size=DEFAULT_PAGE_SIZE)
    items = task_service.tasks_for_project(store, parse_id(project_id, field="project_id"))
    return HTTP_OK, paginate(items, page=page, page_size=size)


def create_task(store, request, project_id):
    task = task_service.create_task(
        store,
        parse_id(project_id, field="project_id"),
        request.body.get("title"),
        priority=request.body.get("priority", DEFAULT_PRIORITY),
    )
    return HTTP_CREATED, task


def search_tasks(store, request):
    page, size = parse_page_params(request.query, default_size=DEFAULT_PAGE_SIZE)
    return HTTP_OK, task_service.search_tasks(store, request.query.get("q", ""), page=page, page_size=size)


def update_task(store, request, task_id):
    return HTTP_OK, task_service.update_task(store, parse_id(task_id, field="task_id"), request.body)
