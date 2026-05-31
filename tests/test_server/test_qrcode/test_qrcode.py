"""Тестовый модуль системы QR-кодов"""

import base64, io
from starlette.testclient import TestClient

class TestQRCodeGeneration:
    def test_generate_qrcode(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/generate", json={"purpose": "attendance"})
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "code" in data
        assert "image_base64" in data
        assert "expires_at" in data
        assert "purpose" in data

    def test_generate_qrcode_for_user_and_get_active_qrcodes(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/generate/for-user/1", json={"purpose": "attendance"})
        assert resp.status_code == 200 
        qrcode_id = resp.json()["id"]

        resp = auth_client.get("/api/v1/generate/active")
        assert resp.status_code == 200
        assert qrcode_id == resp.json()[-1]["id"]

    def test_invalidate_qrcode(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/generate", json={"purpose": "attendance"})
        assert resp.status_code == 200
        qrcode_id = resp.json()["id"]

        resp = auth_client.post(f"/api/v1/generate/{qrcode_id}/invalidate")
        assert resp.status_code == 200
        assert resp.json()["message"] == "QR-код успешно аннулирован"

class TestQRCodeScanning:
    def test_scan_qrcode(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/generate", json={"purpose": "attendance"})
        assert resp.status_code == 200
        data = resp.json()
        qrcode_data = data["code"]
        qrcode_purpose = data["purpose"]

        resp = auth_client.post("/api/v1/scan", json={
            "qr_data": qrcode_data,
            "purpose": qrcode_purpose
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == 1
        assert data["purpose"] == "attendance"

    def test_scan_qrcode_image(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/generate", json={"purpose": "attendance"})
        assert resp.status_code == 200
        data = resp.json()
        qrcode_image_base_64 = data["image_base64"]
        qrcode_purpose = data["purpose"]

        img_bytes = base64.b64decode(qrcode_image_base_64)
        resp = auth_client.post(
            "/api/v1/scan/image",
            files={"file": ("qrcode.png", io.BytesIO(img_bytes), "image/png")},
            data={"purpose": qrcode_purpose},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == 1
        assert data["purpose"] == "attendance"

    def test_create_manual_attendance(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/scan/manual", params={
                                                        "user_id": 1,
                                                        "event_type": "IN"
                                                    })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Запись создана"
        assert data["event_type"] == "IN"

        resp = auth_client.post("/api/v1/scan/manual", params={
                                                        "user_id": 1,
                                                        "event_type": "OUT"
                                                    })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Запись создана"
        assert data["event_type"] == "OUT"

    def test_get_user_current_status(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/scan/manual", params={
                                                        "user_id": 1,
                                                        "event_type": "IN"
                                                    })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Запись создана"
        assert data["event_type"] == "IN"

        resp = auth_client.get("/api/v1/scan/status/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == 1
        assert data["status"] == "inside"
        assert data["last_event"]["type"] == "IN"

class TestQRCodeHistory:
    def test_get_user_history(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/scan/manual", params={
                                                        "user_id": 1,
                                                        "event_type": "IN"
                                                    })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Запись создана"
        assert data["event_type"] == "IN"

        resp = auth_client.get('/api/v1/history/user/1')
        assert resp.status_code == 200
        data = resp.json()
        assert data[-1]["event_type"] == "IN"

    def test_get_my_history(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/scan/manual", params={
                                                        "user_id": 1,
                                                        "event_type": "IN"
                                                    })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Запись создана"
        assert data["event_type"] == "IN"

        resp = auth_client.get('/api/v1/history/me')
        assert resp.status_code == 200
        data = resp.json()
        assert data[-1]["event_type"] == "IN"

    def test_get_attendance_summary(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/history/summary/1")
        assert resp.status_code == 200
        before = resp.json()
        before_events = before.get("total_events", 0)
        before_entries = before.get("total_entries", 0)
        before_exits = before.get("total_exits", 0)

        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "IN"})
        assert resp.status_code == 200
        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "OUT"})
        assert resp.status_code == 200
        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "IN"})
        assert resp.status_code == 200

        resp = auth_client.get("/api/v1/history/summary/1")
        assert resp.status_code == 200
        data = resp.json()

        assert data["user_id"] == 1
        assert "user_name" in data
        assert "period_days" in data
        assert "date_from" in data and "date_to" in data

        assert data["total_events"] == before_events + 3
        assert data["total_entries"] == before_entries + 2
        assert data["total_exits"] == before_exits + 1

        assert isinstance(data["daily_stats"], list)
        last_day = data["daily_stats"][-1]
        assert "date" in last_day
        assert last_day.get("entries", 0) >= 2
        assert last_day.get("exits", 0) >= 1

    def test_get_history_by_date_range(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/history/range", params={
            "date_from": "2020-01-01",
            "date_to": "2027-01-01"
        })
        assert resp.status_code == 200

        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "IN"})
        assert resp.status_code == 200
        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "OUT"})
        assert resp.status_code == 200
        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "IN"})
        assert resp.status_code == 200

        resp = auth_client.get("/api/v1/history/range", params={
            "date_from": "2020-01-01",
            "date_to": "2027-01-01"
        })
        assert resp.status_code == 200
        data = resp.json()

        assert "date_range" in data
        assert data["date_range"]["from"] == "2020-01-01"
        assert data["date_range"]["to"] == "2027-01-01"
        assert data["total_events"] >= 3
        assert data["total_users"] >= 1
        assert "users" in data
        assert "1" in data["users"]
        user_info = data["users"]["1"]
        assert "user_name" in user_info
        assert user_info.get("entries", 0) >= 2
        assert user_info.get("exits", 0) >= 1
        assert isinstance(user_info.get("events", []), list)
        assert len(user_info["events"]) >= 3

    def test_get_user_history_count(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/history/count/1")
        assert resp.status_code == 200

        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "IN"})
        assert resp.status_code == 200
        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "OUT"})
        assert resp.status_code == 200
        resp = auth_client.post("/api/v1/scan/manual", params={"user_id": 1, "event_type": "IN"})
        assert resp.status_code == 200

        resp = auth_client.get("/api/v1/history/count/1")
        assert resp.status_code == 200
        data = resp.json()

        assert data["user_id"] == 1
        assert data["count"] >= 3
        assert "date_from" in data and "date_to" in data