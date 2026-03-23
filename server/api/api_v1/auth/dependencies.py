from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Callable
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from functools import wraps

from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from core.database import get_db
from models import User
from crud.read_methods import get_user_by_login

security = HTTPBearer()


class PermissionChecker:
    """Класс для проверки различных прав доступа."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def user_has_role(self, user: User, role_name: str) -> bool:
        """Проверка наличия конкретной роли."""
        return any(role.name == role_name for role in user.roles)
    
    def user_has_any_role(self, user: User, role_names: List[str]) -> bool:
        """Проверка наличия хотя бы одной из указанных ролей."""
        user_roles = [role.name for role in user.roles]
        return any(role in user_roles for role in role_names)
    
    def user_has_all_roles(self, user: User, role_names: List[str]) -> bool:
        """Проверка наличия всех указанных ролей."""
        user_roles = [role.name for role in user.roles]
        return all(role in user_roles for role in role_names)
    
    def can_access_user_data(self, current_user: User, target_user_id: int) -> bool:
        """Проверка доступа к данным пользователя."""
        if self.user_has_role(current_user, "admin"):
            return True
        
        if current_user.id == target_user_id:
            return True
        
        # Проверка для родителей (доступ к данным детей)
        if self.user_has_role(current_user, "parent"):
            parent = current_user.parent_profile
            if parent:
                child_ids = [student.user_id for student in parent.students]
                if target_user_id in child_ids:
                    return True
        
        # Проверка для учителей (доступ к данным учеников)
        if self.user_has_role(current_user, "teacher"):
            # Здесь можно добавить логику проверки, учит ли учитель этого ученика
            pass
        
        return False


def create_access_token(data: dict) -> str:
    """Создание JWT токена с дополнительными данными."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Декодирование JWT токена."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Недействительный токен: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя по токену."""
    token = credentials.credentials
    payload = decode_token(token)
    
    login = payload.get("sub")
    user_id = payload.get("user_id")
    
    if not login or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_login(db, login)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или неактивен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем, что ID из токена совпадает с ID пользователя
    if user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Несоответствие данных пользователя",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем версию токена для инвалидации сессий
    token_version = payload.get("token_version", 1)
    if user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен недействителен (сессия инвалидирована)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_roles(required_roles: Union[str, List[str]], require_all: bool = False):
    """
    Декоратор для проверки ролей.
    
    Args:
        required_roles: Роль или список ролей
        require_all: Если True, пользователь должен иметь ВСЕ роли
                     Если False, достаточно любой из ролей
    """
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    async def role_checker(current_user: User = Depends(get_current_user)):
        user_roles = [role.name for role in current_user.roles]
        
        if require_all:
            has_required = all(role in user_roles for role in required_roles)
        else:
            has_required = any(role in user_roles for role in required_roles)
        
        if not has_required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуются роли: {', '.join(required_roles)}"
            )
        return current_user
    
    return role_checker


def require_permission(permission_checker: Callable):
    """
    Декоратор для проверки специфических прав.
    
    Args:
        permission_checker: Функция, принимающая (current_user, request, db) и возвращающая bool
    """
    async def permission_dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not permission_checker(current_user, request, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции"
            )
        return current_user
    
    return permission_dependency


def get_permission_checker(db: Session = Depends(get_db)) -> PermissionChecker:
    """Получение экземпляра PermissionChecker."""
    return PermissionChecker(db)