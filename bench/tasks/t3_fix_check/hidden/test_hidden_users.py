def test_unknown_user_uses_app_error(app_client):
    resp = app_client.get("/users/42")
    assert resp.status == 404
    assert resp.body["error"]["code"] == "USER_NOT_FOUND"


def test_comment_limit_still_enforced(app_client):
    assert app_client.post("/tasks/1/comments", {"author_id": 1, "body": "x" * 2000}).status == 201
    assert app_client.post("/tasks/1/comments", {"author_id": 1, "body": "x" * 2001}).status == 422
