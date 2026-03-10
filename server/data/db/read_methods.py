from datetime import datetime
from .models import (
    User, Student, Parent, Grade, Homework,
    AttendanceLog, Notification, Schedule, MealTransaction,
    LibraryLoan, Class, Subject
)


def get_user_by_login(session, login):
    """Получить пользователя по логину"""
    return session.query(User).filter_by(login=login).first()


def get_user_roles(session, user_id):
    """Получить роли пользователя"""
    user = session.query(User).get(user_id)
    return user.roles if user else []


def get_student_by_user_id(session, user_id):
    """Получить студента по ID пользователя"""
    return session.query(Student).filter_by(user_id=user_id).first()


def get_parent_by_user_id(session, user_id):
    """Получить родителя по ID пользователя"""
    return session.query(Parent).filter_by(user_id=user_id).first()


def get_student_grades(session, student_id, subject_id=None):
    """Получить оценки студента"""
    query = session.query(Grade).filter_by(student_id=student_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    return query.all()


def get_class_homeworks(session, class_id):
    """Получить домашние задания для класса"""
    return session.query(Homework).filter_by(class_id=class_id).all()


def get_user_attendance(session, user_id, date_from=None, date_to=None):
    """Получить посещаемость пользователя"""
    query = session.query(AttendanceLog).filter_by(user_id=user_id)
    if date_from:
        query = query.filter(AttendanceLog.timestamp >= date_from)
    if date_to:
        query = query.filter(AttendanceLog.timestamp <= date_to)
    return query.order_by(AttendanceLog.timestamp).all()


def get_user_notifications(session, user_id, unread_only=False):
    """Получить уведомления пользователя"""
    query = session.query(Notification).filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).all()


def get_students_by_parent(session, parent_user_id):
    """Получить студентов по родителю"""
    parent = session.query(Parent).filter_by(user_id=parent_user_id).first()
    if parent:
        return parent.students
    return []


def get_overdue_books(session):
    """Получить список просроченных книг"""
    now = datetime.now()
    return session.query(LibraryLoan).filter(
        LibraryLoan.deadline < now,
        LibraryLoan.returned_at.is_(None)
    ).all()


def get_meal_transactions(session, student_id, limit=50):
    """Получить историю транзакций по питанию"""
    student = session.query(Student).filter_by(user_id=student_id).first()
    if student and student.meal_account:
        return session.query(MealTransaction).filter_by(
            account_id=student.meal_account.id
        ).order_by(MealTransaction.timestamp.desc()).limit(limit).all()
    return []


def check_schedule_conflicts_simple(session, teacher_id, class_id, day_of_week,
                                    lesson_number, exclude_schedule_id=None):
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
        'error_message': _format_conflict_error(session, teacher_conflict, class_conflict)
    }


def _format_conflict_error(session, teacher_conflict, class_conflict):
    """Форматировать сообщение об ошибке конфликта"""
    errors = []

    if teacher_conflict:
        teacher = session.query(User).get(teacher_conflict.teacher_id)
        subject = session.query(Subject).get(teacher_conflict.subject_id)
        class_obj = session.query(Class).get(teacher_conflict.class_id)

        errors.append(
            f"Учитель {teacher.name} уже ведет {subject.name} "
            f"в классе {class_obj.name} в это время"
        )

    if class_conflict:
        class_obj = session.query(Class).get(class_conflict.class_id)
        teacher = session.query(User).get(class_conflict.teacher_id)
        subject = session.query(Subject).get(class_conflict.subject_id)

        errors.append(
            f"Класс {class_obj.name} уже занят уроком {subject.name} "
            f"у учителя {teacher.name}"
        )

    return "\n".join(errors) if errors else None