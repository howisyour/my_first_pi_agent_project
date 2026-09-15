"""User use cases."""

from taskapp.errors import NotFoundError
from taskapp.models_generated import User
from taskapp.storage.repository import get_repo


def get_user_or_404(store, user_id: int) -> User:
    user = get_repo(store, "users").get(user_id)
    if user is None:
        raise NotFoundError(f"user {user_id} not found", code="USER_NOT_FOUND")
    return user


def list_users(store) -> list[User]:
    return get_repo(store, "users").all()
