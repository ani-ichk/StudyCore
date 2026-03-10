from .models import User, Grade, Notification, Student, MealTransaction, TransactionType


def update_user(session, user_id, **kwargs):
    """Обновить данные пользователя"""
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


def update_grade(session, grade_id, **kwargs):
    """Обновить оценку"""
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


def mark_notification_as_read(session, notification_id):
    """Пометить уведомление как прочитанное"""
    try:
        notification = session.query(Notification).get(notification_id)
        if notification:
            notification.is_read = True
            session.commit()
        return notification
    except Exception as e:
        session.rollback()
        raise e


def update_meal_balance(session, student_id, amount):
    """Обновить баланс питания"""
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