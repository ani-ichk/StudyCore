"Тесты для расписания"

from starlette.testclient import TestClient
import datetime

def parse_iso_z(s: str) -> datetime.datetime:
    if s.endswith("Z"):
        s = s[:-1]
    try:
        return datetime.time.fromisoformat(s)
    except ValueError:
        return datetime.datetime.strptime(s, "%H:%M:%S.%f").time()

def test_create_and_delete_schedule(auth_client: TestClient):
    resp = auth_client.post("/api/v1/schedule/", 
                                json={
                                    "class_id": 1,
                                    "subject_id": 1,
                                    "teacher_id": 1,
                                    "classroom_id": 1,
                                    "day_of_week": 1,
                                    "lesson_number": 1,
                                    "start_time": "04:17:18.459Z",
                                    "end_time": "04:47:18.459Z"
                                })
    assert resp.status_code == 201
    schedule_id = resp.json()["id"]
    assert schedule_id is not None
    assert resp.json()["class_id"] == 1
    assert resp.json()["subject_id"] == 1
    assert resp.json()["teacher_id"] == 1
    assert resp.json()["classroom_id"] == 1
    assert resp.json()["day_of_week"] == 1
    assert resp.json()["lesson_number"] == 1
    assert parse_iso_z(resp.json()["start_time"]) == parse_iso_z("04:17:18.459Z")
    assert parse_iso_z(resp.json()["end_time"]) == parse_iso_z("04:47:18.459Z")

    resp = auth_client.delete(f"/api/v1/schedule/{schedule_id}")
    assert resp.status_code == 204

def test_update_schedule(auth_client: TestClient):
    resp = auth_client.post("/api/v1/schedule/", 
                                json={
                                    "class_id": 1,
                                    "subject_id": 2,
                                    "teacher_id": 1,
                                    "classroom_id": 1,
                                    "day_of_week": 1,
                                    "lesson_number": 1,
                                    "start_time": "04:17:18.459Z",
                                    "end_time": "04:47:18.459Z"
                                })
    assert resp.status_code == 201
    schedule_id = resp.json()["id"]

    resp = auth_client.put(f"/api/v1/schedule/{schedule_id}", 
                                      json={
                                        "subject_id": 3,
                                        "teacher_id": 2,
                                        "classroom_id": 2,
                                        "start_time": "05:17:18.459Z",
                                        "end_time": "05:47:18.459Z"
                                    })
    assert resp.status_code == 200
    assert resp.json()["id"] == schedule_id
    assert resp.json()["subject_id"] == 3
    assert resp.json()["teacher_id"] == 2
    assert resp.json()["classroom_id"] == 2
    assert parse_iso_z(resp.json()["start_time"]) == parse_iso_z("05:17:18.459Z")
    assert parse_iso_z(resp.json()["end_time"]) == parse_iso_z("05:47:18.459Z")

    resp = auth_client.delete(f"/api/v1/schedule/{schedule_id}")
    assert resp.status_code == 204

def test_get_schedule(auth_client: TestClient):
    resp = auth_client.post("/api/v1/schedule/", 
                                json={
                                    "class_id": 1,
                                    "subject_id": 4,
                                    "teacher_id": 1,
                                    "classroom_id": 1,
                                    "day_of_week": 1,
                                    "lesson_number": 1,
                                    "start_time": "04:17:18.459Z",
                                    "end_time": "04:47:18.459Z"
                                })
    assert resp.status_code == 201
    schedule_id = resp.json()["id"]

    resp = auth_client.get(f"/api/v1/schedule/{schedule_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == schedule_id
    assert resp.json()["class_id"] == 1
    assert resp.json()["subject_id"] == 4
    assert resp.json()["teacher_id"] == 1
    assert resp.json()["classroom_id"] == 1
    assert resp.json()["day_of_week"] == 1
    assert resp.json()["lesson_number"] == 1
    assert parse_iso_z(resp.json()["start_time"]) == parse_iso_z("04:17:18.459Z")
    assert parse_iso_z(resp.json()["end_time"]) == parse_iso_z("04:47:18.459Z")

    resp = auth_client.delete(f"/api/v1/schedule/{schedule_id}")
    assert resp.status_code == 204

def test_get_schedules_class(auth_client: TestClient):
    resp = auth_client.post("/api/v1/schedule/", 
                                json={
                                    "class_id": 1,
                                    "subject_id": 5,
                                    "teacher_id": 1,
                                    "classroom_id": 1,
                                    "day_of_week": 1,
                                    "lesson_number": 1,
                                    "start_time": "04:17:18.459Z",
                                    "end_time": "04:47:18.459Z"
                                })
    assert resp.status_code == 201
    schedule_id = resp.json()["id"]

    resp = auth_client.get("/api/v1/schedule/class/1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert isinstance(data, list)
    assert data[-1]["id"] == schedule_id
    assert data[-1]["class_id"] == 1
    assert data[-1]["subject_id"] == 5
    assert data[-1]["teacher_id"] == 1
    assert data[-1]["classroom_id"] == 1
    assert data[-1]["day_of_week"] == 1
    assert data[-1]["lesson_number"] == 1
    assert parse_iso_z(data[-1]["start_time"]) == parse_iso_z("04:17:18.459Z")
    assert parse_iso_z(data[-1]["end_time"]) == parse_iso_z("04:47:18.459Z")

    resp = auth_client.delete(f"/api/v1/schedule/{schedule_id}")
    assert resp.status_code == 204

def test_get_schedules_by_teacher_id(auth_client: TestClient):
    resp = auth_client.post("/api/v1/schedule/", 
                                json={
                                    "class_id": 1,
                                    "subject_id": 6,
                                    "teacher_id": 1,
                                    "classroom_id": 1,
                                    "day_of_week": 1,
                                    "lesson_number": 1,
                                    "start_time": "04:17:18.459Z",
                                    "end_time": "04:47:18.459Z"
                                })
    assert resp.status_code == 201
    schedule_id = resp.json()["id"]

    resp = auth_client.get("/api/v1/schedule/teacher/1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert isinstance(data, list)
    assert data[-1]["id"] == schedule_id
    assert data[-1]["class_id"] == 1
    assert data[-1]["subject_id"] == 6
    assert data[-1]["teacher_id"] == 1
    assert data[-1]["classroom_id"] == 1
    assert data[-1]["day_of_week"] == 1
    assert data[-1]["lesson_number"] == 1
    assert parse_iso_z(data[-1]["start_time"]) == parse_iso_z("04:17:18.459Z")
    assert parse_iso_z(data[-1]["end_time"]) == parse_iso_z("04:47:18.459Z")

    resp = auth_client.delete(f"/api/v1/schedule/{schedule_id}")
    assert resp.status_code == 204

def test_get_schedules_by_room(auth_client: TestClient):
    resp = auth_client.post("/api/v1/schedule/", 
                                json={
                                    "class_id": 1,
                                    "subject_id": 7,
                                    "teacher_id": 1,
                                    "classroom_id": 1,
                                    "day_of_week": 1,
                                    "lesson_number": 1,
                                    "start_time": "04:17:18.459Z",
                                    "end_time": "04:47:18.459Z"
                                })
    assert resp.status_code == 201
    schedule_id = resp.json()["id"]

    resp = auth_client.get("/api/v1/schedule/room/1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert isinstance(data, list)
    assert data[-1]["id"] == schedule_id
    assert data[-1]["class_id"] == 1
    assert data[-1]["subject_id"] == 7
    assert data[-1]["teacher_id"] == 1
    assert data[-1]["classroom_id"] == 1
    assert data[-1]["day_of_week"] == 1
    assert data[-1]["lesson_number"] == 1
    assert parse_iso_z(data[-1]["start_time"]) == parse_iso_z("04:17:18.459Z")
    assert parse_iso_z(data[-1]["end_time"]) == parse_iso_z("04:47:18.459Z")

    resp = auth_client.delete(f"/api/v1/schedule/{schedule_id}")
    assert resp.status_code == 204