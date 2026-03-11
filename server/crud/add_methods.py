from server.models import (
    User, UserRole, Student, Parent, Grade, Homework,
    AttendanceLog, Notification, Schedule, NotificationType, Role, MealAccount, Class, Subject
)
from .read_methods import check_schedule_conflicts_simple
from server.scripts.security import PasswordHasher


def add_user(session, login, password, surname, name, patronymic=None,
             phone=None, email=None, is_active=True, **kwargs):
    """Добавить нового пользователя с хэшированием пароля"""
    # Хэшируем пароль
    hashed_password = PasswordHasher.hash_password(password)

    user = User(
        login=login,
        password=hashed_password,
        surname=surname,
        name=name,
        patronymic=patronymic,
        phone=phone,
        email=email,
        is_active=is_active,
        **kwargs
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def add_user_with_roles(session, login, password, surname, name, role_names,
                        patronymic=None, phone=None, email=None, **kwargs):
    """
    Добавить пользователя с назначением ролей

    Args:
        role_names: список названий ролей ['student', 'teacher'] и т.д.
    """
    # Создаем пользователя
    user = add_user(
        session=session,
        login=login,
        password=password,
        surname=surname,
        name=name,
        patronymic=patronymic,
        phone=phone,
        email=email,
        **kwargs
    )

    # Назначаем роли
    for role_name in role_names:
        role = session.query(Role).filter_by(name=role_name).first()
        if role:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            session.add(user_role)

    session.commit()
    return user


def add_student_with_account(session, user_id, class_id, initial_balance=0.0):
    """Добавить студента с созданием счета для питания"""
    student = Student(user_id=user_id, class_id=class_id)
    session.add(student)
    session.flush()  # Получаем ID студента

    # Создаем счет для питания
    meal_account = MealAccount(
        student_id=student.id,
        balance=initial_balance
    )
    session.add(meal_account)

    session.commit()
    session.refresh(student)
    return student

def add_role_to_user(session, user_id, role_id):
    """Добавить роль пользователю"""
    user_role = UserRole(user_id=user_id, role_id=role_id)
    session.add(user_role)
    session.commit()


def add_student(session, user_id, class_id):
    """Добавить студента"""
    student = Student(user_id=user_id, class_id=class_id)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student



def add_parent(session, user_id):
    """Добавить родителя"""
    parent = Parent(user_id=user_id)
    session.add(parent)
    session.commit()
    session.refresh(parent)
    return parent



def add_grade(session, student_id, subject_id, teacher_id, value, comment=None):
    """Добавить оценку"""
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



def add_homework(session, class_id, subject_id, teacher_id, description, deadline):
    """Добавить домашнее задание"""
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


def add_attendance_log(session, user_id, event_type):
    """Добавить запись о посещении"""
    attendance = AttendanceLog(
        user_id=user_id,
        event_type=event_type
    )
    session.add(attendance)
    session.commit()
    session.refresh(attendance)
    return attendance


def add_notification(session, user_id, notification_type, message):
    """Добавить уведомление"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=message
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def add_schedule(session, class_id, subject_id, teacher_id, classroom_id,
                 day_of_week, lesson_number, start_time=None, end_time=None,
                 exclude_schedule_id=None):
    """Добавить запись в расписание с проверкой конфликтов"""
    # Проверяем конфликты перед добавлением
    conflict_check = check_schedule_conflicts_simple(
        session=session,
        teacher_id=teacher_id,
        class_id=class_id,
        day_of_week=day_of_week,
        lesson_number=lesson_number,
        exclude_schedule_id=exclude_schedule_id
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
        classroom_id=classroom_id,
        day_of_week=day_of_week,
        lesson_number=lesson_number,
        start_time=start_time,
        end_time=end_time
    )

    session.add(schedule)
    session.commit()
    session.refresh(schedule)

    # Отправляем уведомления об изменении расписания
    _notify_schedule_change(session, schedule)

    return schedule


def _notify_schedule_change(session, schedule):
    """Отправить уведомления об изменении расписания"""
    # Получаем класс
    class_obj = session.query(Class).get(schedule.class_id)
    subject = session.query(Subject).get(schedule.subject_id)

    # Уведомления для учеников класса
    for student in class_obj.students:
        notification = Notification(
            user_id=student.user_id,
            type=NotificationType.SCHEDULE,
            message=f"Изменение в расписании: {subject.name} "
                    f"в {schedule.day_of_week}-й день, {schedule.lesson_number}-й урок"
        )
        session.add(notification)

        # Уведомления для родителей ученика
        for parent in student.parents:
            notification_parent = Notification(
                user_id=parent.user_id,
                type=NotificationType.SCHEDULE,
                message=f"Изменение в расписании вашего ребенка: {subject.name}"
            )
            session.add(notification_parent)

    # Уведомление для учителя
    notification_teacher = Notification(
        user_id=schedule.teacher_id,
        type=NotificationType.SCHEDULE,
        message=f"Вы добавлены в расписание: {subject.name} "
                f"в классе {class_obj.name}"
    )
    session.add(notification_teacher)

    session.commit()
