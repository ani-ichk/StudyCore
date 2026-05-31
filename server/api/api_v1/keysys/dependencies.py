from sqlalchemy.orm import Session
from models import User, KeyAllowedRole, Role, Key


def can_access_key_room(db: Session, user_id: int, room_id: int) -> bool:
    """
    Проверяет, может ли пользователь получить ключ от кабинета.
    Использует таблицу KeyAllowedRole для проверки прав доступа.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Получаем все роли пользователя
    user_role_names = [r.name for r in user.roles]
    if not user_role_names:
        return False
    
    # Проверяем, есть ли разрешение на этот ключ для любой из ролей пользователя
    allowed = (
        db.query(KeyAllowedRole)
        .join(Key, KeyAllowedRole.key_id == Key.id)
        .filter(
            Key.room_id == room_id,
            KeyAllowedRole.role_name.in_(user_role_names)
        )
        .first()
    )
    
    return allowed is not None


def can_access_key_room_simplified(db: Session, user_id: int, room_id: int) -> bool:
    """
    Упрощённая версия проверки прав доступа.
    Проверяет, есть ли у пользователя роль, разрешённая для ключей этой комнаты.
    """ 
    # Получаем все ключи в этой комнате
    keys_in_room = db.query(Key).filter(Key.room_id == room_id).all()
    
    if not keys_in_room:
        return True  # Если нет ключей в комнате, доступ открыт
    
    # Для каждого ключа проверяем, есть ли разрешение
    for key in keys_in_room:
        allowed_roles = db.query(KeyAllowedRole).filter(
            KeyAllowedRole.key_id == key.id
        ).all()
        
        if allowed_roles:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user_role_names = [role.name for role in user.roles]
                allowed_role_names = [ar.role_name for ar in allowed_roles]
                
                if any(role_name in allowed_role_names for role_name in user_role_names):
                    return True
    
    return False