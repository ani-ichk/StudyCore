from __future__ import annotations

from pathlib import Path
from typing import Final

# --- Настройка FastApi ---
HOST_FAST_API: Final[str] = "127.0.0.1"
PORT_FAST_API: Final[int] = 8080

# --- Путь к проекту ---
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent

# --- Настройки БД ---
DB_FILENAME: Final[str] = "school_system.db"
DB_DIR: Final[Path] = BASE_DIR / "data" 
DB_PATH: Final[Path] = DB_DIR / DB_FILENAME
DB_URL: Final[str] = f"sqlite:///{DB_PATH}"

# --- Токены / авторизация ---
SECRET_KEY: Final[str] = "school-system-very-secret-key-2026-change-me-in-production"
ALGORITHM: Final[str] = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 60 * 24 * 7

# --- Роли / админ ---
DEFAULT_ROLES: Final[list[str]] = ["admin", "teacher", "student", "parent", "staff"]
DEFAULT_ADMIN_LOGIN: Final[str] = "admin"
DEFAULT_ADMIN_PASSWORD: Final[str] = "admin123"
DEFAULT_ADMIN_NAME: Final[str] = "Admin"
DEFAULT_ADMIN_SURNAME: Final[str] = "Admin"
DEFAULT_ADMIN_EMAIL: Final[str] = "admin@admin.ru"
