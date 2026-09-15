"""Comment use cases."""

from taskapp.models_generated import Comment
from taskapp.services.tasks import get_task_or_404
from taskapp.services.users import get_user_or_404
from taskapp.services.validation import validate_comment_body
from taskapp.storage.repository import get_repo


def list_comments(store, task_id: int) -> list[Comment]:
    get_task_or_404(store, task_id)
    return [comment for comment in get_repo(store, "comments").all() if comment.task_id == task_id]


def add_comment(store, task_id: int, author_id: int, body) -> Comment:
    get_task_or_404(store, task_id)
    get_user_or_404(store, author_id)
    clean = validate_comment_body(body)
    return get_repo(store, "comments").add(
        lambda i: Comment(id=i, task_id=task_id, author_id=author_id, body=clean)
    )
