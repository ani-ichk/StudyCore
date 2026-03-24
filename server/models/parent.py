from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Parent(Base):
    """Таблица родителей"""
    __tablename__ = 'parents'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)

    # Связи
    user = relationship("User", back_populates="parent_profile")
    students = relationship("Student", secondary="student_parent", back_populates="parents")