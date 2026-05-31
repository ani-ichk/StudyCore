from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from .base import Base


class Key(Base):
    """Таблица ключей"""
    __tablename__ = 'keys'

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    number = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    status = Column(String(20), default='available', nullable=False)  # available, issued, lost, maintenance
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    room = relationship("Room", back_populates="keys")
    key_logs = relationship("KeyLog", back_populates="key", cascade="all, delete")
    allowed_roles = relationship("KeyAllowedRole", back_populates="key", cascade="all, delete")
    actions = relationship("KeyAction", back_populates="key", cascade="all, delete")


class KeyAllowedRole(Base):
    """Связующая таблица ключей и разрешенных ролей"""
    __tablename__ = 'key_allowed_roles'

    role_name = Column(String(50), ForeignKey('roles.name'), primary_key=True)
    key_id = Column(Integer, ForeignKey('keys.id'), primary_key=True)

    # Связи
    role = relationship("Role", back_populates="key_allowed_roles")
    key = relationship("Key", back_populates="allowed_roles")


class KeyLog(Base):
    """Таблица журнала выдачи ключей"""
    __tablename__ = 'key_logs'

    id = Column(Integer, primary_key=True)
    key_id = Column(Integer, ForeignKey('keys.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    issued_at = Column(DateTime, default=datetime.now)
    returned_at = Column(DateTime)

    # Связи
    key = relationship("Key", back_populates="key_logs")
    user = relationship("User", back_populates="key_logs")


class KeyAction(Base):
    """Таблица логирования действий с ключами"""
    __tablename__ = 'key_actions'

    id = Column(Integer, primary_key=True)
    key_id = Column(Integer, ForeignKey('keys.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action_type = Column(String(50), nullable=False)  # issue, return, report_lost, maintenance_start, maintenance_end
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    key = relationship("Key", back_populates="actions")
    user = relationship("User", back_populates="key_actions")