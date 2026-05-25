from sqlalchemy.orm import Session
from models import Key
from schemas import KeyCreate

# Возможны фулл изменения

def get_key(db: Session, key_id: int):
    return db.query(Key).filter(Key.id == key_id).first()

def get_keys(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Key).offset(skip).limit(limit).all()

def get_available_keys(db: Session):
    return db.query(Key).filter(Key.status == "available").all()

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