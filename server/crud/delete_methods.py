from models import (
    User, Grade, Homework, Notification, Student, Parent,
    QRCode, AttendanceLog, LibraryLoan, KeyLog, KeyAction,
    TeacherSubject, Schedule
)


def delete_user(session, user_id):
    """Удалить пользователя и все связанные с ним данные"""
    user = session.get(User, user_id)
    if not user:
        return False
    
    try:
        # Удаляем оценки, выставленные этим учителем
        session.query(Grade).filter_by(teacher_id=user_id).delete()
        
        # Удаляем домашние задания, созданные этим учителем
        session.query(Homework).filter_by(teacher_id=user_id).delete()
        
        # Удаляем записи расписания этого учителя
        session.query(Schedule).filter_by(teacher_id=user_id).delete()
        
        # Удаляем предметы, преподаваемые этим учителем
        session.query(TeacherSubject).filter_by(teacher_id=user_id).delete()
        
        # Удаляем QR коды
        session.query(QRCode).filter_by(user_id=user_id).delete()
        
        # Удаляем логи посещаемости
        session.query(AttendanceLog).filter_by(user_id=user_id).delete()
        
        # Удаляем уведомления
        session.query(Notification).filter_by(user_id=user_id).delete()
        
        # Удаляем библиотечные выдачи
        session.query(LibraryLoan).filter_by(user_id=user_id).delete()
        
        # Удаляем логи ключей
        session.query(KeyLog).filter_by(user_id=user_id).delete()
        
        # Удаляем действия с ключами
        session.query(KeyAction).filter_by(user_id=user_id).delete()
        
        # Если это студент, удаляем его профиль
        student = session.query(Student).filter_by(user_id=user_id).first()
        if student:
            # Удаляем оценки студента
            session.query(Grade).filter_by(student_id=student.id).delete()
            # Удаляем домашние задания студента
            session.query(Homework).filter_by(student_id=student.id).delete()
            # Удаляем профиль студента
            session.delete(student)
        
        # Если это родитель, удаляем его профиль
        parent = session.query(Parent).filter_by(user_id=user_id).first()
        if parent:
            session.delete(parent)
        
        # Удаляем самого пользователя
        session.delete(user)
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении пользователя: {e}")
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
    notification = session.get(Notification, notification_id)
    if notification:
        session.delete(notification)
        session.commit()
        return True
    return False
