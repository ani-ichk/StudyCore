"""Тест системы ключей"""

from starlette.testclient import TestClient


def test_get_all_keys(auth_client: TestClient):
    resp = auth_client.get("/api/v1/keys/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

def test_create_and_delete_key(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": "string0",
            "room_id": 100,
            "description": "string",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["number"] == "string0"
    assert data["room_id"] == 100
    assert data["status"] == "available"
    assert data["description"] == "string"
    keys_id = data["id"]

    resp = auth_client.delete(f"/api/v1/keys/{keys_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

def test_update_key(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": "string6",
            "room_id": 100,
            "description": "string",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    key_id = data["id"]

    resp = auth_client.put(f"/api/v1/keys/{key_id}/update", json={
            "number": "string6",
            "room_id": 100,
            "description": "updated description",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    resp = auth_client.get(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "updated description"

    resp = auth_client.delete(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

def test_available_keys(auth_client: TestClient):
    resp = auth_client.get("/api/v1/keys/available")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for key in data:
        assert key["status"] == "available"

def test_get_keys_by_id(auth_client: TestClient):
    number = "test-key-123"
    room_id = 999
    description = "Test key for get by ID"
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": number,
            "room_id": room_id,
            "description": description,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    key_id = data["id"]

    resp = auth_client.get(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["number"] == number
    assert data["room_id"] == room_id
    assert data["description"] == description

    resp = auth_client.delete(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True


def test_get_history_key_by_id(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": "string2",
            "room_id": 100,
            "description": "string",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    key_id = data["id"]

    resp = auth_client.get(f"/api/v1/keys/{key_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for action in data:
        assert "key_id" in action

    resp = auth_client.delete(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

def allow_role_for_key(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": "string7",
            "room_id": 100,
            "description": "string",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    key_id = data["id"]
    role_name = "admin"

    resp = auth_client.post(f"/api/v1/keys/{key_id}/role/{role_name}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    resp = auth_client.delete(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

def delete_role_for_key(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": "string8",
            "room_id": 100,
            "description": "string",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    key_id = data["id"]
    role_name = "admin"

    resp = auth_client.post(f"/api/v1/keys/{key_id}/role/{role_name}")
    assert resp.status_code == 200

    resp = auth_client.delete(f"/api/v1/keys/{key_id}/role/{role_name}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    resp = auth_client.delete(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

def test_issue_and_return_key(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": "string3",
            "room_id": 100,
            "description": "string",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    key_id = data["id"]
    role_name = "admin"

    resp = auth_client.post(f"/api/v1/keys/{key_id}/role/{role_name}")
    assert resp.status_code == 200

    resp = auth_client.post(f"/api/v1/keys/{key_id}/issue")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    resp = auth_client.get(f"/api/v1/keys/{key_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["action_type"] == "issue"

    resp = auth_client.post(f"/api/v1/keys/{key_id}/return")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    resp = auth_client.get(f"/api/v1/keys/{key_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["action_type"] == "return"

    resp = auth_client.delete(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

def test_report_lost_key(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": "string4",
            "room_id": 100,
            "description": "string",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    key_id = data["id"]

    resp = auth_client.post(f"/api/v1/keys/{key_id}/report-lost", params={"description": "test lost"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    resp = auth_client.get(f"/api/v1/keys/{key_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["action_type"] == "report_lost"

    resp = auth_client.delete(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

def test_maintenance_key(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/keys/",
        json={
            "number": "string5",
            "room_id": 100,
            "description": "string",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    key_id = data["id"]

    resp = auth_client.post(f"/api/v1/keys/{key_id}/maintenance", params={"description": "test maintenance"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    resp = auth_client.get(f"/api/v1/keys/{key_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["action_type"] == "maintenance_start"
    assert data[0]["description"] == "test maintenance"

    resp = auth_client.post(f"/api/v1/keys/{key_id}/maintenance-complete", params={"description": "test maintenance complete"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True

    resp = auth_client.get(f"/api/v1/keys/{key_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["action_type"] == "maintenance_end"

    resp = auth_client.delete(f"/api/v1/keys/{key_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True