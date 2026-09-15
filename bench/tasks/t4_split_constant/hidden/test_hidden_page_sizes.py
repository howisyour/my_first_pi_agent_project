from pathlib import Path

import taskapp.constants as constants

ROOT = Path(__file__).resolve().parents[1]


def test_constants_split():
    assert constants.LIST_PAGE_SIZE == 25
    assert constants.SEARCH_PAGE_SIZE == 10
    assert not hasattr(constants, "DEFAULT_PAGE_SIZE")


def test_no_references_left():
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "taskapp").rglob("*.py")
        if "DEFAULT_PAGE_SIZE" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_list_endpoints_use_list_page_size(app_client):
    for path in ("/projects/1/tasks", "/projects", "/users"):
        assert app_client.get(path).body["page_size"] == 25, path


def test_search_uses_search_page_size(app_client):
    resp = app_client.get("/tasks/search", {"q": "task"})
    assert resp.body["page_size"] == 10
    assert len(resp.body["items"]) == 10
    assert resp.body["has_next"] is True
