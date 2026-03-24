from models import User, UserRole, Role
from .security import PasswordHasher


def authenticate_user(session, login, password, role_name=None):
    """Аутентификация пользователя с проверкой пароля и роли"""
    user = session.query(User).filter_by(login=login, is_active=True).first()
    
    if user and PasswordHasher.verify_password(password, user.password):
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


def authenticate_user_by_email(session, email, password):
    """Аутентификация по email"""
    user = session.query(User).filter_by(email=email, is_active=True).first()
    
    if user and PasswordHasher.verify_password(password, user.password):
        return user
    return None


def change_password(session, user_id, old_password, new_password):
    """Смена пароля пользователя"""
    try:
        user = session.query(User).get(user_id)
        if not user:
            return False, "Пользователь не найден"

        # Проверяем старый пароль
        if not PasswordHasher.verify_password(old_password, user.password):
            return False, "Неверный текущий пароль"

        # Проверяем новый пароль
        if not PasswordHasher.is_password_strong(new_password):
            return False, "Пароль слишком слабый"

        # Устанавливаем новый пароль
        user.password = PasswordHasher.hash_password(new_password)
        session.commit()

        return True, "Пароль успешно изменен"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка при смене пароля: {str(e)}"


def reset_password(session, user_id, new_password):
    """Сброс пароля (для администратора)"""
    try:
        user = session.query(User).get(user_id)
        if not user:
            return False, "Пользователь не найден"

        # Устанавливаем новый пароль
        user.password = PasswordHasher.hash_password(new_password)
        session.commit()

        return True, "Пароль успешно сброшен"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка при сбросе пароля: {str(e)}"