def test_stats_match_spec(app_client):
    resp = app_client.get("/projects/1/stats")
    assert resp.status == 200
    assert resp.body == {"project_id": 1, "total": 30, "by_status": {"open": 10, "in_progress": 10, "done": 10}}


def test_stats_are_computed_not_hardcoded(app_client):
    assert app_client.patch("/tasks/31", {"status": "done"}).status == 200
    resp = app_client.get("/projects/2/stats")
    assert resp.status == 200
    assert resp.body == {"project_id": 2, "total": 6, "by_status": {"open": 1, "in_progress": 2, "done": 3}}


def test_unknown_project(app_client):
    resp = app_client.get("/projects/999/stats")
    assert resp.status == 404
    assert resp.body["error"]["code"] == "PROJECT_NOT_FOUND"
