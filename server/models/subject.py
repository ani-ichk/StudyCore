from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Subject(Base):
    """Таблица учебных предметов"""
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    # Связи
    teacher_subjects = relationship("TeacherSubject", back_populates="subject")
    homeworks = relationship("Homework", back_populates="subject")
    grades = relationship("Grade", back_populates="subject")
    schedule_entries = relationship("Schedule", back_populates="subject")


class TeacherSubject(Base):
    """Связующая таблица учителей и предметов"""
    __tablename__ = 'teacher_subject'

    teacher_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), primary_key=True)

    # Связи
    teacher = relationship("User", back_populates="teacher_subjects")
    subject = relationship("Subject", back_populates="teacher_subjects")