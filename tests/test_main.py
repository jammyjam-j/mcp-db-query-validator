Open app/main.pyWe need to read files.import os

import pytest
from fastapi.testclient import TestClient

API_KEY = "test-secret-key"
os.environ["API_KEY"] = API_KEY


@pytest.fixture(scope="module")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_create_user_success(client: TestClient):
    user_payload = {"username": "alice", "email": "alice@example.com"}
    response = client.post(
        "/users",
        json=user_payload,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"


def test_get_users_list(client: TestClient):
    response = client.get("/users", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert any(user["username"] == "alice" for user in users)


def test_unauthorized_access(client: TestClient):
    payload = {"username": "bob", "email": "bob@example.com"}
    create_resp = client.post("/users", json=payload)
    assert create_resp.status_code == 401
    get_resp = client.get("/users")
    assert get_resp.status_code == 401


def test_invalid_user_payload(client: TestClient):
    invalid_payloads = [
        {"username": "", "email": "valid@example.com"},
        {"username": "charlie", "email": ""},
        {},
    ]
    for payload in invalid_payloads:
        resp = client.post(
            "/users",
            json=payload,
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 422


def test_user_update_and_delete(client: TestClient):
    # Create user
    create_resp = client.post(
        "/users",
        json={"username": "dave", "email": "dave@example.com"},
        headers={"X-API-Key": API_KEY},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    # Update user
    update_payload = {"username": "dave_updated", "email": "dave_new@example.com"}
    update_resp = client.put(
        f"/users/{user_id}",
        json=update_payload,
        headers={"X-API-Key": API_KEY},
    )
    assert update_resp.status_code == 200
    updated_user = update_resp.json()
    assert updated_user["username"] == "dave_updated"
    assert updated_user["email"] == "dave_new@example.com"

    # Delete user
    delete_resp = client.delete(
        f"/users/{user_id}",
        headers={"X-API-Key": API_KEY},
    )
    assert delete_resp.status_code == 204

    # Verify deletion
    get_resp = client.get(f"/users/{user_id}", headers={"X-API-Key": API_KEY})
    assert get_resp.status_code == 404


def test_query_validator_endpoint(client: TestClient):
    # Assuming the application exposes a /validate-query endpoint for testing purposes.
    query_payload = {"query": "SELECT * FROM users;"}
    resp = client.post(
        "/validate-query",
        json=query_payload,
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert isinstance(result, dict)
    assert result.get("is_valid") is True or result.get("error") is None

def test_invalid_sql_query(client: TestClient):
    query_payload = {"query": "DROP TABLE users;"}
    resp = client.post(
        "/validate-query",
        json=query_payload,
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result.get("is_valid") is False
    assert "error" in result

def test_database_connection_on_startup():
    from app.db import engine
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.scalar_one() == 1
    except Exception as exc:
        pytest.fail(f"Database connection failed: {exc}")