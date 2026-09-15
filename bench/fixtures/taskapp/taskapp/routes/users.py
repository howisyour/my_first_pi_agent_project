"""User routes."""

from taskapp.constants import DEFAULT_PAGE_SIZE, HTTP_OK
from taskapp.services import users as user_service
from taskapp.services.pagination import paginate
from taskapp.utils.ids import parse_id
from taskapp.utils.querystring import parse_page_params


def list_users(store, request):
    page, size = parse_page_params(request.query, default_size=DEFAULT_PAGE_SIZE)
    return HTTP_OK, paginate(user_service.list_users(store), page=page, page_size=size)


def get_user(store, request, user_id):
    return HTTP_OK, user_service.get_user_or_404(store, parse_id(user_id, field="user_id"))
