def test_get_user(app_client):
    resp = app_client.get("/users/1")
    assert resp.status == 200
    assert resp.body["username"] == "ada"


def test_unknown_user_is_404(app_client):
    resp = app_client.get("/users/42")
    assert resp.status == 404
    assert resp.body["error"]["code"] == "USER_NOT_FOUND"
