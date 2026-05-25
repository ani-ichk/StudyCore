"""Конфигурационные файлы для StudyCore."""
from .config import (
    HOST_FAST_API, PORT_FAST_API, BASE_DIR, DB_FILENAME, DB_DIR, 
    DB_PATH, DB_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, 
    DEFAULT_ROLES, DEFAULT_ADMIN_LOGIN, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_NAME, 
    DEFAULT_ADMIN_SURNAME, DEFAULT_ADMIN_EMAIL
)
from .database import (
    get_db, init_db,
)
from .seed import (
    seed_database, 
)

__all__ = [
    'get_db',
    'init_db',
    'seed_database',
    'HOST_FAST_API',
    'PORT_FAST_API',
    'BASE_DIR',
    'DB_FILENAME',
    'DB_DIR',
    'DB_PATH',
    'DB_URL',
    'SECRET_KEY',
    'ALGORITHM',
    'ACCESS_TOKEN_EXPIRE_MINUTES',
    'DEFAULT_ROLES',
    'DEFAULT_ADMIN_LOGIN',
    'DEFAULT_ADMIN_PASSWORD',
    'DEFAULT_ADMIN_NAME',
    'DEFAULT_ADMIN_SURNAME',
    'DEFAULT_ADMIN_EMAIL',
]