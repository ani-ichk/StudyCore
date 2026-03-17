from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Student(Base):
    """Таблица студентов"""
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'))

    # Связи
    user = relationship("User", back_populates="student_profile")
    class_ = relationship("Class", back_populates="students")
    parents = relationship("Parent", secondary="student_parent", back_populates="students")
    meal_account = relationship("MealAccount", uselist=False, back_populates="student")
    grades = relationship("Grade", back_populates="student")
    homeworks = relationship("Homework", back_populates="student")


class StudentParent(Base):
    """Связующая таблица студентов и родителей"""
    __tablename__ = 'student_parent'

    student_id = Column(Integer, ForeignKey('students.id'), primary_key=True)
    parent_id = Column(Integer, ForeignKey('parents.id'), primary_key=True)