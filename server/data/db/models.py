from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    DateTime, Float, Boolean, Enum, Text, Date, Time
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ И ENUM
# ============================================

class EventType(enum.Enum):
    IN = "IN"
    OUT = "OUT"


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class RoomType(enum.Enum):
    CLASSROOM = "classroom"
    LIBRARY = "library"
    STORAGE = "storage_room"
    OTHER = "other"


class NotificationType(enum.Enum):
    ATTENDANCE = "attendance"
    GRADE = "grade"
    LIBRARY = "library"
    SCHEDULE = "schedule"
    MEAL = "meal"
    GENERAL = "general"


# ============================================
# ТАБЛИЦЫ МОДЕЛЕЙ
# ============================================

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


class Role(Base):
    """Таблица ролей пользователей"""
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # admin, teacher, student, parent, staff

    # Связи
    users = relationship("User", secondary="user_roles", back_populates="roles")
    key_allowed_roles = relationship("KeyAllowedRole", back_populates="role")


class UserRole(Base):
    """Связующая таблица пользователей и ролей (многие-ко-многим)"""
    __tablename__ = 'user_roles'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)


class QRCode(Base):
    """Таблица QR-кодов для пользователей"""
    __tablename__ = 'qr_codes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    code = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime)

    # Связи
    user = relationship("User", back_populates="qr_codes")


class Parent(Base):
    """Таблица родителей"""
    __tablename__ = 'parents'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)

    # Связи
    user = relationship("User", back_populates="parent_profile")
    students = relationship("Student", secondary="student_parent", back_populates="parents")


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


class Class(Base):
    """Таблица классов"""
    __tablename__ = 'classes'

    id = Column(Integer, primary_key=True)
    class_teacher_id = Column(Integer, ForeignKey('users.id'))
    classroom_id = Column(Integer, ForeignKey('rooms.id'))
    name = Column(String(20), nullable=False)  # 10А, 5Б и т.д.
    year = Column(Integer, nullable=False)

    # Связи
    class_teacher = relationship("User")
    classroom = relationship("Room")
    students = relationship("Student", back_populates="class_")
    homeworks = relationship("Homework", back_populates="class_")
    schedule_entries = relationship("Schedule", back_populates="class_")


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
    teacher = relationship("User", back_populates="homeworks")


class AttendanceLog(Base):
    """Таблица журнала посещаемости"""
    __tablename__ = 'attendance_log'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)  # IN/OUT
    timestamp = Column(DateTime, default=datetime.now)

    # Связи
    user = relationship("User", back_populates="attendance_logs")


class Notification(Base):
    """Таблица уведомлений"""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    user = relationship("User", back_populates="notifications")


class MealAccount(Base):
    """Таблица счетов для питания"""
    __tablename__ = 'meal_accounts'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), unique=True, nullable=False)
    balance = Column(Float, default=0.0)

    # Связи
    student = relationship("Student", back_populates="meal_account")
    transactions = relationship("MealTransaction", back_populates="account")


class MealTransaction(Base):
    """Таблица транзакций по питанию"""
    __tablename__ = 'meal_transactions'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('meal_accounts.id'), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    description = Column(String(255))

    # Связи
    account = relationship("MealAccount", back_populates="transactions")


class Book(Base):
    """Таблица книг библиотеки"""
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(20))
    quantity_total = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)

    # Связи
    loans = relationship("LibraryLoan", back_populates="book")


class LibraryLoan(Base):
    """Таблица выдачи книг"""
    __tablename__ = 'library_loans'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    issued_at = Column(DateTime, default=datetime.now)
    deadline = Column(DateTime, nullable=False)
    returned_at = Column(DateTime)

    # Связи
    book = relationship("Book", back_populates="loans")
    user = relationship("User", back_populates="library_loans")


class Grade(Base):
    """Таблица оценок"""
    __tablename__ = 'grades'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    value = Column(Integer, nullable=False)  # 2-5 или 1-10
    date = Column(Date, default=datetime.now().date)
    comment = Column(Text)

    # Связи
    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")
    teacher = relationship("User", back_populates="grades_given")


class Room(Base):
    """Таблица помещений"""
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)
    number = Column(String(20), nullable=False)
    description = Column(Enum(RoomType), default=RoomType.CLASSROOM)

    # Связи
    classes = relationship("Class", back_populates="classroom")
    keys = relationship("Key", back_populates="room")
    schedule_entries = relationship("Schedule", back_populates="classroom")


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


class Schedule(Base):
    """Таблица расписания"""
    __tablename__ = 'schedule'

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    classroom_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 1-понедельник, 7-воскресенье
    lesson_number = Column(Integer, nullable=False)  # 1-й урок, 2-й и т.д.
    start_time = Column(Time)
    end_time = Column(Time)

    # Связи
    class_ = relationship("Class", back_populates="schedule_entries")
    subject = relationship("Subject", back_populates="schedule_entries")
    teacher = relationship("User", back_populates="schedule_entries")
    classroom = relationship("Room", back_populates="schedule_entries")