"Тест модуля аутентификации"

from starlette.testclient import TestClient

def restore_admin(client: TestClient):
    resp = client.post("/api/v1/login", json=
                       {"login": "admin", 
                        "password": "admin123"
                        })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return token

class TestAuth:
    def test_login(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/login", json={
            "login": "admin", 
            "password": "admin123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        restore_admin(auth_client)
    
    def test_refresh_token(self, auth_client: TestClient):
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
                                        "teacher"
                                    ]
                                })
        assert resp.status_code == 201
        data = resp.json()
        assert data["login"] == "string"

        resp = auth_client.post("/api/v1/login", 
                           json={
                            "login": "string", 
                            "password": "stri123В!ng"
        })
        assert resp.status_code == 200
        data = resp.json()
        refresh_token = data["refresh_token"]
        auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

        resp = auth_client.post("/api/v1/login/refresh", params={
            "refresh_token": refresh_token
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

        resp = auth_client.get("/api/v1/session/me")
        assert resp.status_code == 200
        data = resp.json()
        user_id = data["id"]
        assert data["login"] == "string"
        assert "teacher" in data["roles"]

        resp = auth_client.delete("/api/v1/session/account")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user_id
        
        restore_admin(auth_client)
    
    def test_check_login(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/login/check", params={"login": "admin"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is True
        assert data["available"] is False

    def test_logout(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/logout")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Успешный выход из системы"
        assert data["user"] == "Admin Admin"

        resp = auth_client.get("/api/v1/session/me")
        assert resp.status_code == 401
        data = resp.json()
        assert data["detail"] == "Токен недействителен (сессия инвалидирована)"

        restore_admin(auth_client)

    def test_logout_all(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/logout/all-devices")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Выполнен выход со всех устройств"
        assert data["user"] == "Admin Admin"

        resp = auth_client.get("/api/v1/session/me")
        assert resp.status_code == 401
        data = resp.json()
        assert data["detail"] == "Токен недействителен (сессия инвалидирована)"
        
        restore_admin(auth_client)
        
class TestSession:
    def test_get_current_session(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/session/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["login"] == "admin"
        assert data["surname"] == "Admin"
        assert data["name"] == "Admin"
        assert data["patronymic"] == None
        assert data["phone"] == None
        assert data["id"] == 1
        assert "admin" in data["roles"]

    def test_verify_session(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/session/verify")
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] == True
        assert data["user_id"] == 1
        assert data["login"] == "admin"
        assert "admin" in data["roles"]

    def test_change_password(self, auth_client: TestClient):
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
                                        "teacher"
                                    ]
                                })
        assert resp.status_code == 201
        data = resp.json()
        assert data["login"] == "string"

        resp = auth_client.post("/api/v1/login", 
                           json={
                            "login": "string", 
                            "password": "stri123В!ng"
        })
        assert resp.status_code == 200
        data = resp.json()
        auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

        resp = auth_client.get("/api/v1/session/me")
        assert resp.status_code == 200
        data = resp.json()

        resp = auth_client.post("/api/v1/session/change-password",
                                params={
                                    "old_password": "stri123В!ng",
                                    "new_password": "stri123В!ng1"
                                })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Пароль успешно изменен"

        resp = auth_client.post("/api/v1/login", 
                           json={
                            "login": "string", 
                            "password": "stri123В!ng1"
        })
        assert resp.status_code == 200
        data = resp.json()
        auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

        resp = auth_client.get("/api/v1/session/me")
        assert resp.status_code == 200
        data = resp.json()
        user_id = data["id"]

        resp = auth_client.delete("/api/v1/session/account")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user_id

        restore_admin(auth_client)

    def test_get_user_permissions(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/session/permissions")
        assert resp.status_code == 200
        data = resp.json()
        assert "permissions" in data

    def test_delete_account(self, auth_client: TestClient):
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
                                        "teacher"
                                    ]
                                })
        assert resp.status_code == 201
        data = resp.json()
        assert data["login"] == "string"
        assert "teacher" in data["roles"]

        resp = auth_client.post("/api/v1/login", 
                           json={
                            "login": "string", 
                            "password": "stri123В!ng"
        })
        assert resp.status_code == 200
        data = resp.json()
        auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

        resp = auth_client.get("/api/v1/session/me")
        assert resp.status_code == 200
        data = resp.json()
        user_id = data["id"]

        resp = auth_client.delete("/api/v1/session/account")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user_id

        restore_admin(auth_client)

class TestRegistration:
    def test_register_user(self, auth_client: TestClient):
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
                                        "teacher"
                                    ]
                                })
        assert resp.status_code == 201
        data = resp.json()
        assert data["login"] == "string"
        assert "teacher" in data["roles"]

        resp = auth_client.post("/api/v1/login", 
                           json={
                            "login": "string", 
                            "password": "stri123В!ng"
        })
        assert resp.status_code == 200
        data = resp.json()
        auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

        resp = auth_client.get("/api/v1/session/me")
        assert resp.status_code == 200
        data = resp.json()
        user_id = data["id"]

        resp = auth_client.delete("/api/v1/session/account")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user_id

        restore_admin(auth_client)

    def test_register_parent_with_child(self, auth_client: TestClient):
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
        
        resp = auth_client.post("/api/v1/register/with-children",
                                json={
                                    "user_data": {
                                        "login": "string1",
                                        "surname": "string",
                                        "name": "string",
                                        "patronymic": "string",
                                        "phone": "string",
                                        "email": "user2@example.com",
                                        "password": "stri123В!ng",
                                        "role_names": [
                                            "parent"
                                        ]
                                    },
                                    "children_ids": [
                                        user_id
                                    ]
                                })
        assert resp.status_code == 200

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

        resp = auth_client.post("/api/v1/login", 
                           json={
                            "login": "string1", 
                            "password": "stri123В!ng"
        })
        assert resp.status_code == 200
        data = resp.json()
        auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

        resp = auth_client.delete("/api/v1/session/account")
        assert resp.status_code == 200

        restore_admin(auth_client)

    def test_register_multiple_users(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/register/batch",
                                json=[
                                        {
                                            "login": "string",
                                            "surname": "string",
                                            "name": "string",
                                            "patronymic": "string",
                                            "phone": "string",
                                            "email": "user@example.com",
                                            "password": "stri123В!ng",
                                            "role_names": [
                                                "teacher"
                                            ]
                                        },
                                        {
                                            "login": "string1",
                                            "surname": "string",
                                            "name": "string",
                                            "patronymic": "string",
                                            "phone": "string",
                                            "email": "user2@example.com",
                                            "password": "stri123В!ng",
                                            "role_names": [
                                                "student"
                                            ]
                                        },  
                                    ])
        assert resp.status_code == 200

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

        resp = auth_client.post("/api/v1/login", 
                           json={
                            "login": "string1", 
                            "password": "stri123В!ng"
        })
        assert resp.status_code == 200
        data = resp.json()
        auth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})

        resp = auth_client.delete("/api/v1/session/account")
        assert resp.status_code == 200

        restore_admin(auth_client)
