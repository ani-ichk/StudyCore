from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from crud import key_system as crud_keys
from .dependencies import can_access_key_room
from models import User, KeyIssue
from datetime import datetime
from api.api_v1.auth.dependencies import require_roles

router = APIRouter(prefix="/keys", tags=["key_system"])


@router.get("/")
def get_all_keys(db: Session = Depends(get_db)):
    return crud_keys.get_keys(db)


@router.get("/available")
def get_available_keys(db: Session = Depends(get_db)):
    return crud_keys.get_available_keys(db)


@router.post("/{key_id}/issue")
def issue_key(
        key_id: int,
        db: Session = Depends(get_db),
        current_user = Depends(require_roles(["admin", "staff"])),
):
    # 1. Получаем ключ из БД
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    if key.status != "available":
        raise HTTPException(status_code=400, detail=f"Ключ {key.number} недоступен")

    # 2. Проверяем права через auth-модуль
    if not can_access_key_room(current_user, key.room):
        raise HTTPException(status_code=403, detail=f"Нет прав на ключ от кабинета {key.room}")

    # 3. Выдаем ключ
    crud_keys.update_key_status(db, key_id, "issued")

    # 4. Записываем в историю (используя модель KeyIssue)
    new_issue = KeyIssue(
        key_id=key_id,
        user_id=current_user.id,
        issue_time=datetime.now()
    )
    db.add(new_issue)
    db.commit()

    return {"message": f"Ключ {key.number} выдан {current_user.name}", "success": True}


@router.post("/{key_id}/return")
def return_key(
        key_id: int,
        db: Session = Depends(get_db),
        current_user = Depends(require_roles(["admin", "staff"])),
):
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    if key.status != "issued":
        raise HTTPException(status_code=400, detail="Ключ не был выдан")

    # Находим активную выдачу
    active_issue = db.query(KeyIssue).filter(
        KeyIssue.key_id == key_id,
        KeyIssue.return_time.is_(None)
    ).first()

    if not active_issue:
        raise HTTPException(status_code=404, detail="Активная выдача не найдена")

    # Проверка, что возвращает тот, кто брал (опционально)
    if active_issue.user_id != current_user.id and current_user.role not in ["admin", "security"]:
        raise HTTPException(status_code=403, detail="Вернуть ключ может только тот, кто брал, или администратор")

    # Возвращаем ключ
    crud_keys.update_key_status(db, key_id, "available")
    active_issue.return_time = datetime.now()
    db.commit()

    return {"message": f"Ключ {key.number} возвращен", "success": True}
