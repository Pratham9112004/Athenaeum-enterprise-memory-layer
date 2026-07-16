"""Integration tests for the auth flow (endpoints + service + repository)."""

from fastapi.testclient import TestClient

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"

CREDS = {"email": "ada@example.com", "password": "Analytical-Engine-1843"}


def _register(client: TestClient, **overrides) -> dict:
    payload = {**CREDS, "full_name": "Ada Lovelace", **overrides}
    return client.post(REGISTER, json=payload).json()


def test_register_returns_token_and_user(client: TestClient):
    resp = client.post(REGISTER, json={**CREDS, "full_name": "Ada"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["email"] == "ada@example.com"
    assert "hashed_password" not in body["user"]


def test_register_normalizes_email_case(client: TestClient):
    client.post(REGISTER, json={"email": "MixedCase@Example.com", "password": "abcdefgh1"})
    # Logging in with a different case resolves to the same account.
    resp = client.post(LOGIN, json={"email": "mixedcase@example.com", "password": "abcdefgh1"})
    assert resp.status_code == 200


def test_duplicate_email_conflicts(client: TestClient):
    client.post(REGISTER, json=CREDS)
    resp = client.post(REGISTER, json=CREDS)
    assert resp.status_code == 409


def test_short_password_rejected(client: TestClient):
    resp = client.post(REGISTER, json={"email": "x@example.com", "password": "short"})
    assert resp.status_code == 422


def test_login_success_sets_refresh_cookie(client: TestClient):
    client.post(REGISTER, json=CREDS)
    resp = client.post(LOGIN, json=CREDS)
    assert resp.status_code == 200
    assert resp.json()["access_token"]
    assert "athenaeum_refresh" in resp.cookies


def test_login_wrong_password_unauthorized(client: TestClient):
    client.post(REGISTER, json=CREDS)
    resp = client.post(LOGIN, json={**CREDS, "password": "wrong-password"})
    assert resp.status_code == 401


def test_login_unknown_user_unauthorized(client: TestClient):
    resp = client.post(LOGIN, json={"email": "ghost@example.com", "password": "whatever12"})
    assert resp.status_code == 401


def test_me_requires_authentication(client: TestClient):
    assert client.get(ME).status_code == 401


def test_me_returns_current_user(client: TestClient):
    token = client.post(REGISTER, json=CREDS).json()["access_token"]
    resp = client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "ada@example.com"


def test_refresh_issues_new_access_token(client: TestClient):
    client.post(REGISTER, json=CREDS)
    client.post(LOGIN, json=CREDS)  # sets cookie on the client's cookie jar
    resp = client.post(REFRESH)
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_refresh_without_cookie_unauthorized(client: TestClient):
    resp = client.post(REFRESH)
    assert resp.status_code == 401


def test_logout_clears_cookie(client: TestClient):
    client.post(REGISTER, json=CREDS)
    client.post(LOGIN, json=CREDS)
    resp = client.post(LOGOUT)
    assert resp.status_code == 204
