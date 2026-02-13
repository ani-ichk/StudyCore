import bcrypt
import hashlib
import secrets
import string
from datetime import datetime, timedelta


class PasswordHasher:
    """Класс для хэширования и проверки паролей"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хэширование пароля с использованием bcrypt
        Возвращает строку в формате: algorithm$salt$hash
        """
        # Генерируем соль и хэшируем пароль
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Возвращаем в формате для хранения
        return f"bcrypt${salt.decode('utf-8')}${hashed.decode('utf-8')}"

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        try:
            # Извлекаем алгоритм, соль и хэш
            parts = hashed_password.split('$')
            if len(parts) != 3 or parts[0] != 'bcrypt':
                # Для обратной совместимости с старыми паролями
                return False

            # Проверяем пароль
            password_bytes = password.encode('utf-8')
            stored_hash = parts[2].encode('utf-8')

            return bcrypt.checkpw(password_bytes, stored_hash)
        except Exception:
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

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in string.punctuation for c in password)

        return has_upper and has_lower and has_digit and has_special


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