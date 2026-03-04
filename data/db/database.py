from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, ForeignKey,
    DateTime, Float, Boolean, Enum, Text, Date, Time
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy import event
import enum
import os

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
    homeworks = relationship("Homework", back_populates="class_")


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
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    class_ = relationship("Class", back_populates="homeworks")
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


# ============================================
# КЛАСС ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# ============================================

class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, db_url="sqlite:///school_system.db"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Получить сессию для работы с БД"""
        return self.SessionLocal()

    # ============================================
    # БЛОК: ИНИЦИАЛИЗАЦИЯ И СИДИРОВАНИЕ ДАННЫХ
    # ============================================

    def initialize_database(self):
        """Инициализация базы данных с начальными данными"""
        session = self.get_session()
        try:
            # Создаем стандартные роли если их нет
            roles = ["admin", "teacher", "student", "parent", "staff"]
            for role_name in roles:
                if not session.query(Role).filter_by(name=role_name).first():
                    session.add(Role(name=role_name))

            # Создаем тестовые предметы если их нет
            subjects = ["Математика", "Русский язык", "Физика", "Химия", "Биология",
                        "История", "Литература", "Иностранный язык", "Информатика"]
            for subject_name in subjects:
                if not session.query(Subject).filter_by(name=subject_name).first():
                    session.add(Subject(name=subject_name))

            # Создаем администратора по умолчанию
            if not session.query(User).filter_by(login="admin").first():
                admin_user = User(
                    login="admin",
                    password="admin123",  # В реальном приложении хэшировать пароль!
                    name="Администратор",
                    patronymic="Системный",
                    phone="+79000000000"
                )
                session.add(admin_user)
                session.flush()

                # Назначаем роль администратора
                admin_role = session.query(Role).filter_by(name="admin").first()
                if admin_role:
                    session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))

            session.commit()
            print("База данных инициализирована успешно")
        except Exception as e:
            session.rollback()
            print(f"Ошибка при инициализации БД: {e}")
        finally:
            session.close()

    # ============================================
    # БЛОК: МЕТОДЫ ДЛЯ ДОБАВЛЕНИЯ ДАННЫХ (CREATE)
    # ============================================

    def add_user(self, login, password, name, patronymic=None, phone=None):
        """Добавить нового пользователя"""
        session = self.get_session()
        try:
            user = User(
                login=login,
                password=password,
                name=name,
                patronymic=patronymic,
                phone=phone
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_role_to_user(self, user_id, role_id):
        """Добавить роль пользователю"""
        session = self.get_session()
        try:
            user_role = UserRole(user_id=user_id, role_id=role_id)
            session.add(user_role)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_student(self, user_id, class_id):
        """Добавить студента"""
        session = self.get_session()
        try:
            student = Student(user_id=user_id, class_id=class_id)
            session.add(student)
            session.commit()
            session.refresh(student)
            return student
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_parent(self, user_id):
        """Добавить родителя"""
        session = self.get_session()
        try:
            parent = Parent(user_id=user_id)
            session.add(parent)
            session.commit()
            session.refresh(parent)
            return parent
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_grade(self, student_id, subject_id, teacher_id, value, comment=None):
        """Добавить оценку"""
        session = self.get_session()
        try:
            grade = Grade(
                student_id=student_id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                value=value,
                comment=comment
            )
            session.add(grade)
            session.commit()
            session.refresh(grade)
            return grade
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_homework(self, class_id, subject_id, teacher_id, description, deadline):
        """Добавить домашнее задание"""
        session = self.get_session()
        try:
            homework = Homework(
                class_id=class_id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                description=description,
                deadline=deadline
            )
            session.add(homework)
            session.commit()
            session.refresh(homework)
            return homework
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_attendance_log(self, user_id, event_type):
        """Добавить запись о посещении"""
        session = self.get_session()
        try:
            attendance = AttendanceLog(
                user_id=user_id,
                event_type=event_type
            )
            session.add(attendance)
            session.commit()
            session.refresh(attendance)
            return attendance
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_notification(self, user_id, notification_type, message):
        """Добавить уведомление"""
        session = self.get_session()
        try:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                message=message
            )
            session.add(notification)
            session.commit()
            session.refresh(notification)
            return notification
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_schedule(self, class_id, subject_id, teacher_id, classroom_id,
                     day_of_week, lesson_number, start_time=None, end_time=None):
        """Добавить запись в расписание с проверкой конфликтов"""

        session = self.get_session()
        try:
            # Проверяем конфликты перед добавлением
            conflict_check = self.check_schedule_conflicts_simple(
                teacher_id=teacher_id,
                class_id=class_id,
                day_of_week=day_of_week,
                lesson_number=lesson_number
            )

            if conflict_check['has_conflicts']:
                raise ValueError(
                    f"Конфликт расписания:\n{conflict_check['error_message']}"
                )

            # Создаем запись расписания
            schedule = Schedule(
                class_id=class_id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                classroom_id=classroom_id,  # Храним для истории, но не проверяем отдельно
                day_of_week=day_of_week,
                lesson_number=lesson_number,
                start_time=start_time,
                end_time=end_time
            )

            session.add(schedule)
            session.commit()
            session.refresh(schedule)

            # Отправляем уведомления об изменении расписания
            self._notify_schedule_change(schedule)

            return schedule

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


def _notify_schedule_change(self, schedule):
    """Отправить уведомления об изменении расписания"""
    session = self.get_session()
    try:
        # Получаем класс
        class_obj = session.query(Class).get(schedule.class_id)

        # Уведомления для учеников класса
        for student in class_obj.students:
            notification = Notification(
                user_id=student.user_id,
                type=NotificationType.SCHEDULE,
                message=f"Изменение в расписании: {schedule.subject.name} "
                        f"в {schedule.day_of_week}-й день, {schedule.lesson_number}-й урок"
            )
            session.add(notification)

            # Уведомления для родителей ученика
            for parent in student.parents:
                notification_parent = Notification(
                    user_id=parent.user_id,
                    type=NotificationType.SCHEDULE,
                    message=f"Изменение в расписании вашего ребенка: {schedule.subject.name}"
                )
                session.add(notification_parent)

        # Уведомление для учителя
        notification_teacher = Notification(
            user_id=schedule.teacher_id,
            type=NotificationType.SCHEDULE,
            message=f"Вы добавлены в расписание: {schedule.subject.name} "
                    f"в классе {class_obj.name}"
        )
        session.add(notification_teacher)

        session.commit()

    except Exception as e:
        print(f"Ошибка при отправке уведомлений: {e}")
    finally:
        session.close()

    # ============================================
    # БЛОК: МЕТОДЫ ДЛЯ ПОЛУЧЕНИЯ ДАННЫХ (READ)
    # ============================================

    def get_user_by_login(self, login):
        """Получить пользователя по логину"""
        session = self.get_session()
        try:
            return session.query(User).filter_by(login=login).first()
        finally:
            session.close()

    def get_user_roles(self, user_id):
        """Получить роли пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).get(user_id)
            return user.roles if user else []
        finally:
            session.close()

    def get_student_by_user_id(self, user_id):
        """Получить студента по ID пользователя"""
        session = self.get_session()
        try:
            return session.query(Student).filter_by(user_id=user_id).first()
        finally:
            session.close()

    def get_parent_by_user_id(self, user_id):
        """Получить родителя по ID пользователя"""
        session = self.get_session()
        try:
            return session.query(Parent).filter_by(user_id=user_id).first()
        finally:
            session.close()

    def get_student_grades(self, student_id, subject_id=None):
        """Получить оценки студента"""
        session = self.get_session()
        try:
            query = session.query(Grade).filter_by(student_id=student_id)
            if subject_id:
                query = query.filter_by(subject_id=subject_id)
            return query.all()
        finally:
            session.close()

    def get_class_homeworks(self, class_id):
        """Получить домашние задания для класса"""
        session = self.get_session()
        try:
            return session.query(Homework).filter_by(class_id=class_id).all()
        finally:
            session.close()

    def get_user_attendance(self, user_id, date_from=None, date_to=None):
        """Получить посещаемость пользователя"""
        session = self.get_session()
        try:
            query = session.query(AttendanceLog).filter_by(user_id=user_id)
            if date_from:
                query = query.filter(AttendanceLog.timestamp >= date_from)
            if date_to:
                query = query.filter(AttendanceLog.timestamp <= date_to)
            return query.order_by(AttendanceLog.timestamp).all()
        finally:
            session.close()

    def get_user_notifications(self, user_id, unread_only=False):
        """Получить уведомления пользователя"""
        session = self.get_session()
        try:
            query = session.query(Notification).filter_by(user_id=user_id)
            if unread_only:
                query = query.filter_by(is_read=False)
            return query.order_by(Notification.created_at.desc()).all()
        finally:
            session.close()

    # ============================================
    # БЛОК: МЕТОДЫ ДЛЯ ОБНОВЛЕНИЯ ДАННЫХ (UPDATE)
    # ============================================

    def update_user(self, user_id, **kwargs):
        """Обновить данные пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).get(user_id)
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                session.commit()
                session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_grade(self, grade_id, **kwargs):
        """Обновить оценку"""
        session = self.get_session()
        try:
            grade = session.query(Grade).get(grade_id)
            if grade:
                for key, value in kwargs.items():
                    if hasattr(grade, key):
                        setattr(grade, key, value)
                session.commit()
                session.refresh(grade)
            return grade
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def mark_notification_as_read(self, notification_id):
        """Пометить уведомление как прочитанное"""
        session = self.get_session()
        try:
            notification = session.query(Notification).get(notification_id)
            if notification:
                notification.is_read = True
                session.commit()
            return notification
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_meal_balance(self, student_id, amount):
        """Обновить баланс питания"""
        session = self.get_session()
        try:
            student = session.query(Student).filter_by(user_id=student_id).first()
            if student and student.meal_account:
                student.meal_account.balance += amount

                # Создаем запись о транзакции
                transaction_type = TransactionType.DEPOSIT if amount > 0 else TransactionType.WITHDRAWAL
                transaction = MealTransaction(
                    account_id=student.meal_account.id,
                    amount=abs(amount),
                    transaction_type=transaction_type
                )
                session.add(transaction)

                session.commit()
                return student.meal_account.balance
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ============================================
    # БЛОК: МЕТОДЫ ДЛЯ УДАЛЕНИЯ ДАННЫХ (DELETE)
    # ============================================

    def delete_user(self, user_id):
        """Удалить пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).get(user_id)
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_grade(self, grade_id):
        """Удалить оценку"""
        session = self.get_session()
        try:
            grade = session.query(Grade).get(grade_id)
            if grade:
                session.delete(grade)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_homework(self, homework_id):
        """Удалить домашнее задание"""
        session = self.get_session()
        try:
            homework = session.query(Homework).get(homework_id)
            if homework:
                session.delete(homework)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_notification(self, notification_id):
        """Удалить уведомление"""
        session = self.get_session()
        try:
            notification = session.query(Notification).get(notification_id)
            if notification:
                session.delete(notification)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ============================================
    # БЛОК: СПЕЦИАЛЬНЫЕ МЕТОДЫ ДЛЯ БИЗНЕС-ЛОГИКИ
    # ============================================

    def authenticate_user(self, login, password, role_name=None):
        """Аутентификация пользователя с проверкой роли"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(login=login, password=password).first()
            if user:
                if role_name:
                    # Проверяем, есть ли у пользователя указанная роль
                    role = session.query(Role).filter_by(name=role_name).first()
                    if role:
                        user_role = session.query(UserRole).filter_by(
                            user_id=user.id, role_id=role.id
                        ).first()
                        return user if user_role else None
                return user
            return None
        finally:
            session.close()

    def get_students_by_parent(self, parent_user_id):
        """Получить студентов по родителю"""
        session = self.get_session()
        try:
            parent = session.query(Parent).filter_by(user_id=parent_user_id).first()
            if parent:
                return parent.students
            return []
        finally:
            session.close()

    def check_schedule_conflicts_simple(self, teacher_id, class_id, day_of_week,
                                        lesson_number, exclude_schedule_id=None):
        """
        Упрощенная проверка конфликтов расписания
        В ТЗ указано только две проверки:
        1. Учитель не может быть на двух уроках одновременно
        2. В одном классе не может быть два урока одновременно
        """

        session = self.get_session()
        try:
            # Находим все записи в расписании на это время
            conflicting_entries = session.query(Schedule).filter(
                Schedule.day_of_week == day_of_week,
                Schedule.lesson_number == lesson_number,
                (
                        (Schedule.teacher_id == teacher_id) |  # Учитель уже занят
                        (Schedule.class_id == class_id)  # Класс уже занят
                )
            )

            # Исключаем текущую запись при редактировании
            if exclude_schedule_id:
                conflicting_entries = conflicting_entries.filter(
                    Schedule.id != exclude_schedule_id
                )

            conflicting_entries = conflicting_entries.all()

            # Анализируем результаты
            teacher_conflict = None
            class_conflict = None

            for entry in conflicting_entries:
                if entry.teacher_id == teacher_id:
                    teacher_conflict = entry
                if entry.class_id == class_id:
                    class_conflict = entry

            return {
                'has_conflicts': len(conflicting_entries) > 0,
                'teacher_conflict': teacher_conflict is not None,
                'class_conflict': class_conflict is not None,
                'conflicting_entries': conflicting_entries,
                'error_message': self._format_conflict_error(teacher_conflict, class_conflict)
            }
        finally:
            session.close()


    def _format_conflict_error(self, teacher_conflict, class_conflict):
        """Форматировать сообщение об ошибке конфликта"""
        errors = []

        if teacher_conflict:
            # Получаем информацию об учителе
            session = self.get_session()
            try:
                teacher = session.query(User).get(teacher_conflict.teacher_id)
                subject = session.query(Subject).get(teacher_conflict.subject_id)
                class_obj = session.query(Class).get(teacher_conflict.class_id)

                errors.append(
                    f"Учитель {teacher.get_full_name()} уже ведет {subject.name} "
                    f"в классе {class_obj.name} в это время"
                )
            finally:
                session.close()

        if class_conflict:
            # Получаем информацию о классе
            session = self.get_session()
            try:
                class_obj = session.query(Class).get(class_conflict.class_id)
                teacher = session.query(User).get(class_conflict.teacher_id)
                subject = session.query(Subject).get(class_conflict.subject_id)

                errors.append(
                    f"Класс {class_obj.name} уже занят уроком {subject.name} "
                    f"у учителя {teacher.get_full_name()}"
                )
            finally:
                session.close()

        return "\n".join(errors) if errors else None

    def get_overdue_books(self):
        """Получить список просроченных книг"""
        session = self.get_session()
        try:
            from datetime import datetime
            now = datetime.now()
            return session.query(LibraryLoan).filter(
                LibraryLoan.deadline < now,
                LibraryLoan.returned_at.is_(None)
            ).all()
        finally:
            session.close()

    def get_meal_transactions(self, student_id, limit=50):
        """Получить историю транзакций по питанию"""
        session = self.get_session()
        try:
            student = session.query(Student).filter_by(user_id=student_id).first()
            if student and student.meal_account:
                return session.query(MealTransaction).filter_by(
                    account_id=student.meal_account.id
                ).order_by(MealTransaction.timestamp.desc()).limit(limit).all()
            return []
        finally:
            session.close()


# ============================================
# УТИЛИТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def hash_password(password: str) -> str:
    """Хэширование пароля (заглушка, в реальном приложении использовать bcrypt или аналоги)"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def generate_qr_code_data(user_id: int) -> str:
    """Генерация данных для QR-кода"""
    import uuid
    from datetime import datetime, timedelta
    return f"school_system:{user_id}:{uuid.uuid4()}:{datetime.now().timestamp()}"


# ============================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================

if __name__ == "__main__":
    # Создание и инициализация базы данных
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    print("Модели и менеджер базы данных готовы к использованию")