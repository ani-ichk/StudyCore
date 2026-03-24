from models import User, Grade, Homework, Notification


def delete_user(session, user_id):
    """Удалить пользователя"""
    user = session.query(User).get(user_id)
    if user:
        session.delete(user)
        session.commit()
        return True
    return False



def delete_grade(session, grade_id):
    """Удалить оценку"""
    grade = session.query(Grade).get(grade_id)
    if grade:
        session.delete(grade)
        session.commit()
        return True
    return False



def delete_homework(session, homework_id):
    """Удалить домашнее задание"""
    homework = session.query(Homework).get(homework_id)
    if homework:
        session.delete(homework)
        session.commit()
        return True
    return False


def delete_notification(session, notification_id):
    """Удалить уведомление"""
    notification = session.query(Notification).get(notification_id)
    if notification:
        session.delete(notification)
        session.commit()
        return True
    return False
