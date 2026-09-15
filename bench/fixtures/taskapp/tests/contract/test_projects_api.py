def test_get_project(app_client):
    resp = app_client.get("/projects/1")
    assert resp.status == 200
    assert resp.body["name"] == "Project 1"


def test_unknown_project_is_404(app_client):
    resp = app_client.get("/projects/999")
    assert resp.status == 404
    assert resp.body["error"]["code"] == "PROJECT_NOT_FOUND"


def test_list_projects_is_paginated(app_client):
    resp = app_client.get("/projects")
    assert resp.status == 200
    assert resp.body["page"] == 1
    assert [project["id"] for project in resp.body["items"]] == [1, 2]


def test_archived_project_rejects_new_tasks(app_client):
    assert app_client.post("/projects/2/archive").status == 200
    resp = app_client.post("/projects/2/tasks", {"title": "late"})
    assert resp.status == 409
    assert resp.body["error"]["code"] == "PROJECT_ARCHIVED"
