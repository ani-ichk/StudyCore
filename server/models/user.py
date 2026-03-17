from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    """Основная таблица пользователей"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    patronymic = Column(String(100))
    phone = Column(String(20))
    email = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)

    # Связи
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    qr_codes = relationship("QRCode", back_populates="user")
    attendance_logs = relationship("AttendanceLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    library_loans = relationship("LibraryLoan", back_populates="user")
    key_logs = relationship("KeyLog", back_populates="user")
    teacher_subjects = relationship("TeacherSubject", back_populates="teacher")
    grades_given = relationship("Grade", foreign_keys="[Grade.teacher_id]", back_populates="teacher")
    homeworks = relationship("Homework", foreign_keys="[Homework.teacher_id]", back_populates="teacher")
    schedule_entries = relationship("Schedule", foreign_keys="[Schedule.teacher_id]", back_populates="teacher")

    # Для родительской роли
    parent_profile = relationship("Parent", uselist=False, back_populates="user")
    # Для студенческой роли
    student_profile = relationship("Student", uselist=False, back_populates="user")

