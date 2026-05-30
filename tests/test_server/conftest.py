from collections.abc import Generator
from pathlib import Path
from typing import Union
import sys
import os
import datetime

import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# запуск с папки server/
ROOT_DIR = Path(__file__).resolve().parents[2] / "server"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from main import app
from core import database, seed_database
from models import Base

@pytest.fixture(scope="session")
def temp_db_file(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("data") / "test.sqlite"

@pytest.fixture(scope="session")
def test_engine(temp_db_file):
    db_url = f"sqlite:///{temp_db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()

@pytest.fixture(scope="session", autouse=True)
def setup_test_db(test_engine, temp_db_file):
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        seed_database(session)
    finally:
        session.close()
    database.engine = test_engine
    database.SessionLocal = TestSessionLocal
    yield
    try:
        os.remove(temp_db_file)
    except OSError:
        pass

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

def restore_admin(client: TestClient):
    resp = client.post("/api/v1/login", json=
                       {"login": "admin", 
                        "password": "admin123"
                        })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return token

def parse_iso_z(s: str) -> Union[datetime.datetime, datetime.time]:
    if not isinstance(s, str):
        raise TypeError("s must be a str")

    # datetime.datetime
    d = s[:-1] + "+00:00" if s.endswith("Z") else s
    try:
        dt = datetime.datetime.fromisoformat(d)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError:
        pass

    # datetime.time
    t = s[:-1] if s.endswith("Z") else s
    try:
        return datetime.time.fromisoformat(t)
    except ValueError:
        for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
            try:
                return datetime.datetime.strptime(t, fmt).time()
            except ValueError:
                continue
        raise ValueError(f"Некорректный формат времени: {s}")