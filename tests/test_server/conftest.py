from collections.abc import Generator
from pathlib import Path
import sys

import pytest
from starlette.testclient import TestClient

# запуск с папки server/
ROOT_DIR = Path(__file__).resolve().parents[2] / "server"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from main import app

@pytest.fixture()
def client() -> Generator[TestClient]:
    with TestClient(app=app) as client:
        yield client

@pytest.fixture()
def auth_client(client: TestClient) -> TestClient:
    resp = client.post("/api/v1/login", json={"login": "admin", "password": "admin123"})
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client