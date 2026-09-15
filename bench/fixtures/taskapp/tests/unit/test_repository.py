from taskapp.models_generated import User
from taskapp.storage.memory import InMemoryStore
from taskapp.storage.repository import get_repo


def test_add_assigns_incrementing_ids():
    repo = get_repo(InMemoryStore(), "users")
    first = repo.add(lambda i: User(id=i, username="a"))
    second = repo.add(lambda i: User(id=i, username="b"))
    assert (first.id, second.id) == (1, 2)


def test_all_is_sorted_by_id():
    store = InMemoryStore()
    repo = get_repo(store, "users")
    repo.add(lambda i: User(id=i, username="a"))
    repo.add(lambda i: User(id=i, username="b"))
    assert [user.username for user in repo.all()] == ["a", "b"]
