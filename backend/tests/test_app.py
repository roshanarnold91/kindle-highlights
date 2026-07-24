def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_login_requires_valid_credentials(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_login_succeeds_with_bootstrap_admin(client):
    resp = client.post(
        "/api/auth/login", json={"username": "admin", "password": "test-admin-password"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["user"]["username"] == "admin"
    assert data["user"]["is_admin"] is True


def test_books_endpoint_requires_auth(client):
    resp = client.get("/api/books")
    assert resp.status_code == 401


def test_books_endpoint_works_after_login(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "test-admin-password"})
    resp = client.get("/api/books")
    assert resp.status_code == 200
    assert resp.get_json() == {"books": []}
