from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from server.models.base import Base


class Homework(Base):
    """Таблица домашних заданий"""
    __tablename__ = 'homeworks'

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    class_ = relationship("Class", back_populates="homeworks")
    student = relationship("Student", back_populates="homeworks")
    subject = relationship("Subject", back_populates="homeworks")
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="homeworks")