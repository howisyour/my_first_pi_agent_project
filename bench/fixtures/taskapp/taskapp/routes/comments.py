"""Comment routes."""

from taskapp.constants import HTTP_CREATED, HTTP_OK
from taskapp.services import comments as comment_service
from taskapp.utils.ids import parse_id, parse_positive_int


def list_comments(store, request, task_id):
    return HTTP_OK, comment_service.list_comments(store, parse_id(task_id, field="task_id"))


def add_comment(store, request, task_id):
    author_id = parse_positive_int(str(request.body.get("author_id", "")), field="author_id")
    comment = comment_service.add_comment(
        store, parse_id(task_id, field="task_id"), author_id, request.body.get("body")
    )
    return HTTP_CREATED, comment
