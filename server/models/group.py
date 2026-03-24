from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Class(Base):
    """Таблица классов"""
    __tablename__ = 'classes'

    id = Column(Integer, primary_key=True)
    class_teacher_id = Column(Integer, ForeignKey('users.id'))
    classroom_id = Column(Integer, ForeignKey('rooms.id'))
    name = Column(String(20), nullable=False)   # 10А, 5Б и т.д.
    year = Column(Integer, nullable=False)

    # Связи
    class_teacher = relationship("User", foreign_keys=[class_teacher_id])
    classroom = relationship("Room", foreign_keys=[classroom_id])
    students = relationship("Student", back_populates="class_")
    homeworks = relationship("Homework", back_populates="class_")
    schedule_entries = relationship("Schedule", back_populates="class_")