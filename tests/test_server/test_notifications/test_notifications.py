"""Тестовый модуль системы увемедомлений"""

from starlette.testclient import TestClient
from tests.test_server.conftest import restore_admin

def test_create_and_delete_notification(auth_client: TestClient):
    resp = auth_client.post("/api/v1/notifications",
                            json={
                                "user_id": 1,
                                "type": "attendance",
                                "message": "string"
                            })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert data["type"] == "attendance"
    assert data["message"] == "string"

    notification_id = data["id"]

    resp = auth_client.delete(f"/api/v1/notifications/{notification_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True

def test_get_user_notifications(auth_client: TestClient):
    resp = auth_client.post("/api/v1/notifications",
                            json={
                                "user_id": 1,
                                "type": "attendance",
                                "message": "get_user_notifications"
                            })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert data["type"] == "attendance"
    assert data["message"] == "get_user_notifications"

    notification_id = data["id"]

    resp = auth_client.get("/api/v1/notifications/me", params={
        "unread_only": False
        }) 
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[-1]["message"] == "get_user_notifications" 
    assert data[-1]["id"] == notification_id

    resp = auth_client.delete(f"/api/v1/notifications/{notification_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True

def test_get_notifications_by_user_for_admin(auth_client: TestClient):
    resp = auth_client.post("/api/v1/register",
                                json={
                                    "login": "string",
                                    "surname": "string",
                                    "name": "string",
                                    "patronymic": "string",
                                    "phone": "string",
                                    "email": "user@example.com",
                                    "password": "stri123В!ng",
                                    "role_names": [
                                        "student"
                                    ]
                                })
    assert resp.status_code == 201
    data = resp.json()
    assert data["login"] == "string"
    assert "student" in data["roles"]
    user_id = data["id"]

    resp = auth_client.post("/api/v1/notifications",
                            json={
                                "user_id": user_id,
                                "type": "attendance",
                                "message": "get_user_notifications_by_admin"
                            })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == user_id
    assert data["type"] == "attendance"
    assert data["message"] == "get_user_notifications_by_admin"
    notification_id = data["id"]

    resp = auth_client.get(f"/api/v1/notifications/user/{user_id}",
                           params={"unread_only": False})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[-1]["message"] == "get_user_notifications_by_admin" 
    assert data[-1]["id"] == notification_id
    
    resp = auth_client.delete(f"/api/v1/notifications/{notification_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True

    resp = auth_client.post("/api/v1/login", 
                           json={
                            "login": "string", 
                            "password": "stri123В!ng"
        })
    assert resp.status_code == 200
    data = resp.json()
    auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

    resp = auth_client.delete("/api/v1/session/account")
    assert resp.status_code == 200

    restore_admin(auth_client)

def test_mark_notification(auth_client: TestClient):
    resp = auth_client.post("/api/v1/notifications",
                            json={
                                "user_id": 1,
                                "type": "attendance",
                                "message": "string"
                            })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert data["type"] == "attendance"
    assert data["message"] == "string"

    notification_id = data["id"]

    resp = auth_client.get("/api/v1/notifications/me", params={
        "unread_only": True
        }) 
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[-1]["message"] == "string" 
    assert data[-1]["id"] == notification_id

    resp = auth_client.patch(f"/api/v1/notifications/{notification_id}/read")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_read"] == True

    resp = auth_client.get("/api/v1/notifications/me", params={
        "unread_only": True
        }) 
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0

    resp = auth_client.delete(f"/api/v1/notifications/{notification_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True
    
def test_unread_notification_count(auth_client: TestClient):
    resp = auth_client.get("/api/v1/notifications/unread/count")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread_count"] == 0

    resp = auth_client.post("/api/v1/notifications",
                            json={
                                "user_id": 1,
                                "type": "attendance",
                                "message": "string"
                            })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert data["type"] == "attendance"
    assert data["message"] == "string"

    notification_id = data["id"]

    resp = auth_client.get("/api/v1/notifications/unread/count")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread_count"] == 1

    resp = auth_client.delete(f"/api/v1/notifications/{notification_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True

def test_mark_all_as_read_notifications(auth_client: TestClient):
    resp = auth_client.get("/api/v1/notifications/unread/count")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread_count"] == 0

    resp = auth_client.post("/api/v1/notifications",
                            json={
                                "user_id": 1,
                                "type": "attendance",
                                "message": "string"
                            })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert data["type"] == "attendance"
    assert data["message"] == "string"

    notification_id_one = data["id"]

    resp = auth_client.post("/api/v1/notifications",
                            json={
                                "user_id": 1,
                                "type": "attendance",
                                "message": "string"
                            })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert data["type"] == "attendance"
    assert data["message"] == "string"

    notification_id_two = data["id"]

    resp = auth_client.get("/api/v1/notifications/unread/count")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread_count"] == 2

    resp = auth_client.post("api/v1/notifications/me/mark-all-read")
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Все уведомления прочитаны"

    resp = auth_client.get("/api/v1/notifications/unread/count")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread_count"] == 0

    resp = auth_client.delete(f"/api/v1/notifications/{notification_id_one}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True

    resp = auth_client.delete(f"/api/v1/notifications/{notification_id_two}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True
    