from sqlalchemy.orm import Session
from models import User, KeyAllowedRole


def can_access_key_room(db: Session, user_id: int, room_id: int) -> bool:
    """
    Проверяет, может ли пользователь получить ключ от кабинета.
    Использует таблицу KeyAllowedRole для проверки прав доступа.
    """
    from models import User, Role
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Получаем все роли пользователя
    user_roles = db.query(Role).join(
        db.query(User).filter(User.id == user_id).first().roles.__class__
    ).all()
    
    # Проверяем, есть ли разрешение на этот ключ для любой из ролей пользователя
    allowed = db.query(KeyAllowedRole).filter(
        KeyAllowedRole.role_id.in_([role.id for role in user.roles]),
        KeyAllowedRole.key_id.in_(
            db.query(db.func.count()).filter(True).from_statement(
                # Получаем ID ключей для этой комнаты
                "SELECT key.id FROM keys WHERE keys.room_id = :room_id"
            ).params(room_id=room_id)
        )
    ).first()
    
    return allowed is not None


def can_access_key_room_simplified(db: Session, user_id: int, room_id: int) -> bool:
    """
    Упрощённая версия проверки прав доступа.
    Проверяет, есть ли у пользователя роль, разрешённая для ключей этой комнаты.
    """
    from models import Key
    
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
                user_role_ids = [role.id for role in user.roles]
                allowed_role_ids = [ar.role_id for ar in allowed_roles]
                
                if any(role_id in allowed_role_ids for role_id in user_role_ids):
                    return True
    
    return False