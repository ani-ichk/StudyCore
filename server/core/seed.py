"""Логика заполнения базы данных (роли, пользователь-администратор, ключи и т.д.)."""

from sqlalchemy.orm import Session
from .config import (
    DEFAULT_ROLES,
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_NAME,
    DEFAULT_ADMIN_SURNAME,
    DEFAULT_ADMIN_EMAIL,
)
from models import Role, User, UserRole, Key, KeyAllowedRole, Room
from scripts import PasswordHasher


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
    
    # Создание комнат, если их нет
    rooms = {}
    room_data = [
        ("101", "CLASSROOM"),
        ("102", "CLASSROOM"),
        ("201", "CLASSROOM"),
        ("LIB", "LIBRARY"),
        ("STR", "STORAGE"),
    ]
    
    for room_number, room_desc in room_data:
        room = session.query(Room).filter_by(number=room_number).first()
        if not room:
            room = Room(number=room_number, description=room_desc)
            session.add(room)
            session.flush()
        rooms[room_number] = room
    
    # Создание ключей
    key_data = [
        ("KEY-101-001", rooms["101"], "Ключ от кабинета 101"),
        ("KEY-102-001", rooms["102"], "Ключ от кабинета 102"),
        ("KEY-201-001", rooms["201"], "Ключ от кабинета 201"),
        ("KEY-LIB-001", rooms["LIB"], "Ключ от библиотеки"),
        ("KEY-STR-001", rooms["STR"], "Ключ от склада"),
    ]
    
    for key_number, room, key_desc in key_data:
        existing_key = session.query(Key).filter_by(number=key_number).first()
        if not existing_key:
            key = Key(
                number=key_number,
                room_id=room.id,
                description=key_desc,
                status="available"
            )
            session.add(key)
            session.flush()
            
            # Добавляем разрешения для разных ролей
            admin_role = session.query(Role).filter_by(name="admin").first()
            staff_role = session.query(Role).filter_by(name="staff").first()
            
            if admin_role:
                admin_perm = session.query(KeyAllowedRole).filter_by(
                    key_id=key.id,
                    role_id=admin_role.id
                ).first()
                if not admin_perm:
                    session.add(KeyAllowedRole(key_id=key.id, role_id=admin_role.id))
            
            if staff_role:
                staff_perm = session.query(KeyAllowedRole).filter_by(
                    key_id=key.id,
                    role_id=staff_role.id
                ).first()
                if not staff_perm:
                    session.add(KeyAllowedRole(key_id=key.id, role_id=staff_role.id))
    
    session.commit()
    print("База данных успешно заполнена начальными данными")