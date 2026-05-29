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