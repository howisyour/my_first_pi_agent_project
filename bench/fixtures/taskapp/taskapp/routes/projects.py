"""Project routes."""

from taskapp.constants import DEFAULT_PAGE_SIZE, HTTP_CREATED, HTTP_OK
from taskapp.services import projects as project_service
from taskapp.services.pagination import paginate
from taskapp.utils.ids import parse_id, parse_positive_int
from taskapp.utils.querystring import parse_page_params


def list_projects(store, request):
    page, size = parse_page_params(request.query, default_size=DEFAULT_PAGE_SIZE)
    return HTTP_OK, paginate(project_service.list_projects(store), page=page, page_size=size)


def get_project(store, request, project_id):
    return HTTP_OK, project_service.get_project_or_404(store, parse_id(project_id, field="project_id"))


def create_project(store, request):
    owner_id = parse_positive_int(str(request.body.get("owner_id", "")), field="owner_id")
    return HTTP_CREATED, project_service.create_project(store, request.body.get("name"), owner_id)


def archive_project(store, request, project_id):
    return HTTP_OK, project_service.archive_project(store, parse_id(project_id, field="project_id"))
