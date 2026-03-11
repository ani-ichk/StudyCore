from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from server.models.base import Base


class Key(Base):
    """Таблица ключей"""
    __tablename__ = 'keys'

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)

    # Связи
    room = relationship("Room", back_populates="keys")
    key_logs = relationship("KeyLog", back_populates="key")
    allowed_roles = relationship("KeyAllowedRole", back_populates="key")


class KeyAllowedRole(Base):
    """Связующая таблица ключей и разрешенных ролей"""
    __tablename__ = 'key_allowed_roles'

    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
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