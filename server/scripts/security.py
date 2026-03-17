import re
import bcrypt
import secrets
import string
from datetime import datetime


class PasswordHasher:
    """Класс для хэширования и проверки паролей"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хэширование пароля с использованием bcrypt
        Возвращает строку в формате: $2b$12$...
        """
        # Генерируем соль и хэшируем пароль
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Возвращаем только хэш (bcrypt уже включает соль)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        try:
            # Просто проверяем пароль с сохраненным хэшем
            password_bytes = password.encode('utf-8')
            stored_hash = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(password_bytes, stored_hash)
        except Exception as e:
            return False

    @staticmethod
    def generate_strong_password(length=12) -> str:
        """Генерация сильного пароля"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    def is_password_strong(password: str) -> bool:
        """Проверка силы пароля"""
        if len(password) < 8:
            return False
        
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        # Требуем минимум 3 из 4 критериев для большей гибкости
        criteria_met = sum([has_upper, has_lower, has_digit, has_special])
        return criteria_met >= 3


class TokenManager:
    """Управление токенами (для API, сброса пароля и т.д.)"""

    @staticmethod
    def generate_token(length=32) -> str:
        """Генерация безопасного токена"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_reset_token() -> str:
        """Генерация токена для сброса пароля"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_api_token(user_id: int) -> str:
        """Генерация API токена для пользователя"""
        timestamp = int(datetime.now().timestamp())
        random_part = secrets.token_urlsafe(16)
        return f"api_{user_id}_{timestamp}_{random_part}"