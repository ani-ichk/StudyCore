from sqlalchemy.orm import Session

from server.core.config import (
    DEFAULT_ROLES,
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_NAME,
    DEFAULT_ADMIN_SURNAME,
)

from .main import db_manager
from .models import Role, User
from .add_methods import add_user_with_roles


def ensure_roles(session: Session, role_names: list[str] = DEFAULT_ROLES) -> None:
    """Создаем базовые роли, если их нет"""
    for role_name in role_names:
        if not session.query(Role).filter_by(name=role_name).first():
            session.add(Role(name=role_name))
    session.commit()


def ensure_admin(
    session: Session,
    login: str = DEFAULT_ADMIN_LOGIN,
    password: str = DEFAULT_ADMIN_PASSWORD,
    surname: str = DEFAULT_ADMIN_SURNAME,
    name: str = DEFAULT_ADMIN_NAME,
    role_names: list[str] = ("admin",),
) -> None:
    """Создаем административного пользователя, если его нет"""
    if session.query(User).filter_by(login=login).first():
        return

    ensure_roles(session, list(role_names))

    add_user_with_roles(
        session=session,
        login=login,
        password=password,
        surname=surname,
        name=name,
        role_names=list(role_names),
    )


def init_db() -> None:
    """Инициализация базы данных (выполняется при старте сервера)."""
    session = db_manager.get_session()
    try:
        ensure_roles(session)
        ensure_admin(session)
    finally:
        session.close()
