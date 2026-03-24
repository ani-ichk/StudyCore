import hashlib
import uuid
from datetime import datetime


def hash_password(password: str) -> str:
    """Хэширование пароля (заглушка, в реальном приложении использовать bcrypt или аналоги)"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_qr_code_data(user_id: int) -> str:
    """Генерация данных для QR-кода"""
    return f"school_system:{user_id}:{uuid.uuid4()}:{datetime.now().timestamp()}"