from .models import User, Grade, Homework, Notification


def delete_user(session, user_id):
    """Удалить пользователя"""
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


def delete_grade(session, grade_id):
    """Удалить оценку"""
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


def delete_homework(session, homework_id):
    """Удалить домашнее задание"""
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


def delete_notification(session, notification_id):
    """Удалить уведомление"""
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