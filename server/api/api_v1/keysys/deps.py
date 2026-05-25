from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.user import User  # предполагаемая модель

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

def get_current_user_with_permission(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Функция, объединяющая получение пользователя и его прав"""
    user = get_current_user(db, token)  # существующая функция из auth
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    return user