from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Role(Base):
    """Таблица ролей пользователей"""
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False) # admin, teacher, student, parent, staff


    # Связи
    users = relationship("User", secondary="user_roles", back_populates="roles")
    key_allowed_roles = relationship("KeyAllowedRole", back_populates="role")


class UserRole(Base):
    """Связующая таблица пользователей и ролей"""
    __tablename__ = 'user_roles'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)