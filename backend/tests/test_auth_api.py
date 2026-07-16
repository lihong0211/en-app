from unittest.mock import patch


def test_register_success(client):
    resp = client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["token"]
    assert body["data"]["user"]["username"] == "alice"
    assert "password" not in body["data"]["user"]


def test_register_duplicate_username(client):
    client.post("/auth/register", json={"username": "bob", "password": "secret123"})
    resp = client.post("/auth/register", json={"username": "bob", "password": "other"})
    body = resp.json()
    assert body["code"] != 200


def test_login_success(client):
    client.post("/auth/register", json={"username": "carol", "password": "secret123"})
    resp = client.post("/auth/login", json={"username": "carol", "password": "secret123"})
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["token"]


def test_login_wrong_password(client):
    client.post("/auth/register", json={"username": "dave", "password": "secret123"})
    resp = client.post("/auth/login", json={"username": "dave", "password": "wrong"})
    body = resp.json()
    assert body["code"] != 200


def test_login_unknown_username(client):
    resp = client.post("/auth/login", json={"username": "nosuchuser", "password": "x"})
    body = resp.json()
    assert body["code"] != 200


def test_me_without_token(client):
    resp = client.get("/auth/me")
    body = resp.json()
    assert body["code"] == 401


def test_me_with_valid_token(client):
    register_resp = client.post(
        "/auth/register", json={"username": "erin", "password": "secret123"}
    )
    token = register_resp.json()["data"]["token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["username"] == "erin"


@patch("api.auth.fetch_wechat_userinfo")
@patch("api.auth.exchange_code_for_openid")
def test_wechat_login_creates_new_user(mock_exchange, mock_userinfo, client):
    mock_exchange.return_value = {"access_token": "AT", "openid": "OPENID_XYZ"}
    mock_userinfo.return_value = {"nickname": "微信昵称", "headimgurl": "https://x.com/a.png"}

    resp = client.post("/auth/wechat/login", json={"code": "some_code"})
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["token"]
    assert body["data"]["user"]["nickname"] == "微信昵称"


@patch("api.auth.fetch_wechat_userinfo")
@patch("api.auth.exchange_code_for_openid")
def test_wechat_login_existing_user_reuses_row(mock_exchange, mock_userinfo, client):
    mock_exchange.return_value = {"access_token": "AT", "openid": "OPENID_SAME"}
    mock_userinfo.return_value = {"nickname": "老用户", "headimgurl": ""}

    first = client.post("/auth/wechat/login", json={"code": "code1"})
    second = client.post("/auth/wechat/login", json={"code": "code2"})

    assert first.json()["data"]["user"]["id"] == second.json()["data"]["user"]["id"]
