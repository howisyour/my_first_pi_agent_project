def test_add_comment_strips_body(app_client):
    resp = app_client.post("/tasks/1/comments", {"author_id": 2, "body": "  hi  "})
    assert resp.status == 201
    assert resp.body["body"] == "hi"


def test_comment_too_long_is_rejected(app_client):
    resp = app_client.post("/tasks/1/comments", {"author_id": 2, "body": "x" * 2001})
    assert resp.status == 422
    assert resp.body["error"]["code"] == "INVALID_COMMENT"


def test_comment_on_unknown_task_is_404(app_client):
    resp = app_client.get("/tasks/999/comments")
    assert resp.status == 404
    assert resp.body["error"]["code"] == "TASK_NOT_FOUND"
