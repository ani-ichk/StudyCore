from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User  # предполагаемая модель
from core import get_db
from api.api_v1.auth.dependencies import get_current_user, require_roles

# Возможна полная переделка кода

# Маппинг ролей на допустимые комнаты (можно вынести в БД или конфиг)
ROOM_PERMISSIONS = {
    "teacher": ["101", "102", "201", "202", "TCH"],
    "security": ["101", "102", "201", "202", "LIB", "DIR", "TCH"],
    "librarian": ["LIB"],
    "admin": ["101", "102", "201", "202", "LIB", "DIR", "TCH"],
    "head_teacher": ["101", "102", "201", "202", "LIB", "DIR", "TCH"],
}

def can_access_key_room(user: User, room: str) -> bool:
    """Проверяет, может ли пользователь получить ключ от кабинета"""
    user_role = user.role  # предполагается, что у User есть поле role
    allowed_rooms = ROOM_PERMISSIONS.get(user_role, [])
    return room in allowed_rooms