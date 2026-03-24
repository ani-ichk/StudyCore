"""Логика заполнения базы данных (роли, пользователь-администратор и т.д.)."""

from sqlalchemy.orm import Session
from core.config import (
    DEFAULT_ROLES,
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_NAME,
    DEFAULT_ADMIN_SURNAME,
    DEFAULT_ADMIN_EMAIL,
)
from models import Role, User, UserRole
from scripts.security import PasswordHasher


def seed_database(session: Session) -> None:
    """Заполнение базы данных начальными данными."""
    
    # Создание ролей
    roles = {}
    for role_name in DEFAULT_ROLES:
        role = session.query(Role).filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name)
            session.add(role)
            session.flush()
        roles[role_name] = role
    
    # Создание администратора
    admin = session.query(User).filter_by(login=DEFAULT_ADMIN_LOGIN).first()
    if not admin:
        admin = User(
            login=DEFAULT_ADMIN_LOGIN,
            password=PasswordHasher.hash_password(DEFAULT_ADMIN_PASSWORD),
            surname=DEFAULT_ADMIN_SURNAME,
            name=DEFAULT_ADMIN_NAME,
            email=DEFAULT_ADMIN_EMAIL,
            is_active=True
        )
        session.add(admin)
        session.flush()
        
        # Назначение роли администратора
        admin_role = session.query(Role).filter_by(name="admin").first()
        if admin_role:
            user_role = UserRole(user_id=admin.id, role_id=admin_role.id)
            session.add(user_role)
    
    session.commit()
    print("База данных успешно заполнена начальными данными")