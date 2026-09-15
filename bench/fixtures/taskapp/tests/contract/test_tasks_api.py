def test_list_tasks_first_page(app_client):
    resp = app_client.get("/projects/1/tasks")
    assert resp.status == 200
    assert len(resp.body["items"]) == resp.body["page_size"]
    assert resp.body["has_next"] is True


def test_create_task_validates_priority(app_client):
    resp = app_client.post("/projects/1/tasks", {"title": "x", "priority": 9})
    assert resp.status == 422
    assert resp.body["error"]["code"] == "INVALID_PRIORITY"


def test_update_task_status(app_client):
    resp = app_client.patch("/tasks/1", {"status": "done"})
    assert resp.status == 200
    assert resp.body["status"] == "done"


def test_search_tasks_filters_by_title(app_client):
    resp = app_client.get("/tasks/search", {"q": "of project 2"})
    assert resp.status == 200
    assert {task["project_id"] for task in resp.body["items"]} == {2}
