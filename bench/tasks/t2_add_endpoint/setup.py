SPEC = '''def test_project_stats_counts_tasks_by_status(app_client):
    resp = app_client.get("/projects/1/stats")
    assert resp.status == 200
    assert resp.body == {"project_id": 1, "total": 30, "by_status": {"open": 10, "in_progress": 10, "done": 10}}


def test_project_stats_unknown_project_is_404(app_client):
    resp = app_client.get("/projects/999/stats")
    assert resp.status == 404
    assert resp.body["error"]["code"] == "PROJECT_NOT_FOUND"
'''


def apply(workdir):
    (workdir / "tests/contract/test_project_stats_api.py").write_text(SPEC, encoding="utf-8", newline="\n")
