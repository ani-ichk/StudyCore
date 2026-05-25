from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Key, KeyAction, KeyLog
from schemas import KeyCreate


def get_key(db: Session, key_id: int):
    return db.query(Key).filter(Key.id == key_id).first()


def get_key_by_number(db: Session, number: str):
    return db.query(Key).filter(Key.number == number).first()


def get_keys(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Key).offset(skip).limit(limit).all()


def get_available_keys(db: Session):
    return db.query(Key).filter(Key.status == "available").all()


def get_keys_by_room(db: Session, room_id: int):
    return db.query(Key).filter(Key.room_id == room_id).all()


def create_key(db: Session, key: KeyCreate):
    db_key = Key(**key.model_dump())
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key


def update_key_status(db: Session, key_id: int, status: str):
    key = get_key(db, key_id)
    if key:
        key.status = status
        db.commit()
        db.refresh(key)
    return key


def update_key(db: Session, key_id: int, **kwargs):
    key = get_key(db, key_id)
    if key:
        for field, value in kwargs.items():
            if hasattr(key, field):
                setattr(key, field, value)
        db.commit()
        db.refresh(key)
    return key


def delete_key(db: Session, key_id: int):
    key = get_key(db, key_id)
    if key:
        db.delete(key)
        db.commit()
        return True
    return False


def create_key_action(db: Session, key_id: int, user_id: int, action_type: str, description: str = None):
    action = KeyAction(
        key_id=key_id,
        user_id=user_id,
        action_type=action_type,
        description=description
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def get_key_actions(db: Session, key_id: int, skip: int = 0, limit: int = 100):
    return db.query(KeyAction).filter(
        KeyAction.key_id == key_id
    ).order_by(desc(KeyAction.created_at)).offset(skip).limit(limit).all()


def get_user_key_actions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(KeyAction).filter(
        KeyAction.user_id == user_id
    ).order_by(desc(KeyAction.created_at)).offset(skip).limit(limit).all()


def get_key_action(db: Session, action_id: int):
    return db.query(KeyAction).filter(KeyAction.id == action_id).first()


# KeyLog CRUD operations
def create_key_log(db: Session, key_id: int, user_id: int):
    log = KeyLog(key_id=key_id, user_id=user_id)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_key_log(db: Session, log_id: int):
    return db.query(KeyLog).filter(KeyLog.id == log_id).first()


def get_active_key_log(db: Session, key_id: int):
    """Получить активный журнал выдачи ключа (еще не возвращен)"""
    return db.query(KeyLog).filter(
        KeyLog.key_id == key_id,
        KeyLog.returned_at.is_(None)
    ).first()


def get_key_logs(db: Session, key_id: int, skip: int = 0, limit: int = 100):
    return db.query(KeyLog).filter(
        KeyLog.key_id == key_id
    ).order_by(desc(KeyLog.issued_at)).offset(skip).limit(limit).all()


def update_key_log_return(db: Session, log_id: int):
    """Отметить возврат ключа"""
    from datetime import datetime
    log = get_key_log(db, log_id)
    if log:
        log.returned_at = datetime.now()
        db.commit()
        db.refresh(log)
    return log