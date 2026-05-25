from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core import get_db
from crud import key_system as crud_keys
from .dependencies import can_access_key_room
from models import User
from api.api_v1.auth.dependencies import require_roles
from schemas.key_system import KeyCreate, KeyOut, KeyListOut, KeyHistoryOut

router = APIRouter(prefix="/keys", tags=["key_system"])


@router.get("/", response_model=list[KeyListOut])
def get_all_keys(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить все ключи"""
    keys = crud_keys.get_keys(db, skip=skip, limit=limit)
    return keys


@router.get("/available", response_model=list[KeyListOut])
def get_available_keys(db: Session = Depends(get_db)):
    """Получить доступные ключи"""
    keys = crud_keys.get_available_keys(db)
    return keys


@router.get("/{key_id}", response_model=KeyOut)
def get_key(key_id: int, db: Session = Depends(get_db)):
    """Получить информацию о ключе"""
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    return key


@router.get("/{key_id}/history", response_model=list[KeyHistoryOut])
def get_key_history(
    key_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить историю действий с ключом"""
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    
    actions = crud_keys.get_key_actions(db, key_id, skip=skip, limit=limit)
    result = []
    for action in actions:
        result.append({
            "id": action.id,
            "key_id": action.key_id,
            "key_number": key.number,
            "user_id": action.user_id,
            "user_name": action.user.name if action.user else "Unknown",
            "action_type": action.action_type,
            "description": action.description,
            "created_at": action.created_at
        })
    return result


@router.post("/", response_model=KeyOut)
def create_key(
    key: KeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """Создать новый ключ (только админ)"""
    # Проверяем, не существует ли ключ с таким номером
    existing_key = crud_keys.get_key_by_number(db, key.number)
    if existing_key:
        raise HTTPException(status_code=400, detail=f"Ключ с номером {key.number} уже существует")
    
    db_key = crud_keys.create_key(db, key)
    
    # Логируем создание ключа
    crud_keys.create_key_action(
        db,
        key_id=db_key.id,
        user_id=current_user.id,
        action_type="created",
        description=f"Ключ создан пользователем {current_user.name}"
    )
    
    return db_key


@router.post("/{key_id}/issue")
def issue_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "staff", "security"])),
):
    """Выдать ключ"""
    # Получаем ключ
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    if key.status != "available":
        raise HTTPException(status_code=400, detail=f"Ключ {key.number} недоступен (статус: {key.status})")

    # Проверяем права доступа
    if not can_access_key_room(db, current_user.id, key.room_id):
        raise HTTPException(status_code=403, detail=f"Нет прав на ключ от кабинета {key.room.number if key.room else 'unknown'}")

    # Создаем запись в журнале
    log = crud_keys.create_key_log(db, key_id=key_id, user_id=current_user.id)
    
    # Обновляем статус ключа
    crud_keys.update_key_status(db, key_id, "issued")

    # Логируем действие
    crud_keys.create_key_action(
        db,
        key_id=key_id,
        user_id=current_user.id,
        action_type="issue",
        description=f"Ключ выдан {current_user.name}"
    )

    return {
        "message": f"Ключ {key.number} выдан {current_user.name}",
        "success": True,
        "log_id": log.id
    }


@router.post("/{key_id}/return")
def return_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "staff", "security"])),
):
    """Вернуть ключ"""
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    if key.status != "issued":
        raise HTTPException(status_code=400, detail="Ключ не был выдан")

    # Находим активный журнал выдачи
    active_log = crud_keys.get_active_key_log(db, key_id)
    if not active_log:
        raise HTTPException(status_code=404, detail="Активная выдача ключа не найдена")

    # Проверка, что возвращает тот, кто брал, или администратор
    if active_log.user_id != current_user.id:
        user_roles = [role.name for role in current_user.roles]
        if "admin" not in user_roles and "security" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail="Вернуть ключ может только тот, кто брал, или администратор"
            )

    # Возвращаем ключ
    crud_keys.update_key_log_return(db, active_log.id)
    crud_keys.update_key_status(db, key_id, "available")

    # Логируем действие
    crud_keys.create_key_action(
        db,
        key_id=key_id,
        user_id=current_user.id,
        action_type="return",
        description=f"Ключ возвращен {current_user.name}"
    )

    return {
        "message": f"Ключ {key.number} возвращен",
        "success": True,
        "log_id": active_log.id
    }


@router.post("/{key_id}/report-lost")
def report_key_lost(
    key_id: int,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "staff", "security"])),
):
    """Сообщить о потере ключа"""
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    # Обновляем статус
    crud_keys.update_key_status(db, key_id, "lost")

    # Закрываем активную выдачу, если есть
    active_log = crud_keys.get_active_key_log(db, key_id)
    if active_log:
        crud_keys.update_key_log_return(db, active_log.id)

    # Логируем действие
    crud_keys.create_key_action(
        db,
        key_id=key_id,
        user_id=current_user.id,
        action_type="report_lost",
        description=description or f"Ключ потерян. Сообщил {current_user.name}"
    )

    return {
        "message": f"Ключ {key.number} отмечен как потерянный",
        "success": True
    }


@router.post("/{key_id}/maintenance")
def start_maintenance(
    key_id: int,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "staff"])),
):
    """Начать обслуживание ключа"""
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    if key.status != "available":
        raise HTTPException(status_code=400, detail="Ключ должен быть доступен для начала обслуживания")

    # Обновляем статус
    crud_keys.update_key_status(db, key_id, "maintenance")

    # Логируем действие
    crud_keys.create_key_action(
        db,
        key_id=key_id,
        user_id=current_user.id,
        action_type="maintenance_start",
        description=description or f"Обслуживание начато {current_user.name}"
    )

    return {
        "message": f"Ключ {key.number} отправлен на обслуживание",
        "success": True
    }


@router.post("/{key_id}/maintenance-complete")
def complete_maintenance(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "staff"])),
):
    """Завершить обслуживание ключа"""
    key = crud_keys.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    if key.status != "maintenance":
        raise HTTPException(status_code=400, detail="Ключ не в процессе обслуживания")

    # Обновляем статус обратно на доступный
    crud_keys.update_key_status(db, key_id, "available")

    # Логируем действие
    crud_keys.create_key_action(
        db,
        key_id=key_id,
        user_id=current_user.id,
        action_type="maintenance_end",
        description=f"Обслуживание завершено {current_user.name}"
    )

    return {
        "message": f"Ключ {key.number} вернулся в обслуживание",
        "success": True
    }
