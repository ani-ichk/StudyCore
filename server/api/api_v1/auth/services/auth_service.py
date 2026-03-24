from sqlalchemy.orm import Session
from typing import Optional, Tuple
from datetime import datetime

from models import User
from scripts.auth_methods import authenticate_user
from crud.add_methods import add_attendance_log
from crud.update_methods import update_user
from schemas import UserResponse


class AuthService:
    """Сервис для бизнес-логики аутентификации."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate(self, login: str, password: str) -> Optional[User]:
        """
        Аутентификация пользователя.
        
        Args:
            login: Логин пользователя
            password: Пароль
            
        Returns:
            Объект пользователя или None
        """
        return authenticate_user(self.db, login, password)
    
    def validate_user_active(self, user: User) -> Tuple[bool, Optional[str]]:
        """
        Проверка, активен ли пользователь.
        
        Args:
            user: Объект пользователя
            
        Returns:
            Кортеж (успех, сообщение об ошибке)
        """
        if not user.is_active:
            return False, "Учетная запись деактивирована. Обратитесь к администратору."
        return True, None
    
    def record_login_attendance(self, user_id: int) -> None:
        """
        Запись события входа в журнал посещаемости.
        
        Args:
            user_id: ID пользователя
        """
        try:
            add_attendance_log(self.db, user_id, "IN")
        except Exception as e:
            # Логируем ошибку, но не прерываем вход
            print(f"Ошибка при создании записи посещаемости: {e}")
    
    def record_logout_attendance(self, user_id: int) -> None:
        """
        Запись события выхода в журнал посещаемости.
        
        Args:
            user_id: ID пользователя
        """
        try:
            add_attendance_log(self.db, user_id, "OUT")
        except Exception as e:
            print(f"Ошибка при создании записи выхода: {e}")
    
    def update_last_login(self, user_id: int) -> None:
        """
        Обновление времени последнего входа.
        
        Args:
            user_id: ID пользователя
        """
        try:
            # Если в модели есть поле last_login
            # update_user(self.db, user_id, last_login=datetime.now())
            pass
        except Exception as e:
            print(f"Ошибка при обновлении времени входа: {e}")
    
    def create_user_response(self, user: User) -> UserResponse:
        """
        Создание ответа с данными пользователя.
        
        Args:
            user: Объект пользователя
            
        Returns:
            UserResponse схема
        """
        return UserResponse(
            id=user.id,
            login=user.login,
            surname=user.surname,
            name=user.name,
            patronymic=user.patronymic,
            phone=user.phone,
            email=user.email,
            is_active=user.is_active,
            roles=[role.name for role in user.roles]
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Получение пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Объект пользователя или None
        """
        return self.db.query(User).get(user_id)
    
    def check_user_exists(self, login: str) -> bool:
        """
        Проверка существования пользователя по логину.
        
        Args:
            login: Логин пользователя
            
        Returns:
            True если пользователь существует
        """
        return self.db.query(User).filter_by(login=login).first() is not None