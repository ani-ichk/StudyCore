from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core import get_db
from models import User, Notification
from schemas import NotificationCreate, NotificationOut, NotificationListOut
from crud import add_notification, get_user_notifications, mark_notification_as_read, delete_notification
from api.api_v1.auth.dependencies import get_current_user, require_roles, get_permission_checker

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationOut)
async def create_notification(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "staff", "teacher"]))
):
    """Отправить уведомление пользователю"""
    user = db.query(User).get(data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return add_notification(db, data.user_id, data.type, data.message)


@router.get("/me", response_model=List[NotificationListOut])
async def get_my_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Мои уведомления"""
    return get_user_notifications(db, current_user.id, unread_only)


@router.get("/user/{user_id}", response_model=List[NotificationListOut])
async def get_user_notifications_by_admin(
    user_id: int,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "staff", "teacher"])),
    perm_checker = Depends(get_permission_checker)
):
    """Уведомления пользователя (для админа/учителя)"""
    if not perm_checker.can_access_user_data(current_user, user_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    return get_user_notifications(db, user_id, unread_only)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_as_read_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Пометить уведомление как прочитанное"""
    notification = db.query(Notification).get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    
    if notification.user_id != current_user.id and "admin" not in [r.name for r in current_user.roles]:
        raise HTTPException(status_code=403, detail="Это не ваше уведомление")
    
    return mark_notification_as_read(db, notification_id)


@router.delete("/{notification_id}")
async def delete_notification_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "staff"]))
):
    """Удалить уведомление (только админ/персонал)"""
    notification = db.query(Notification).get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    
    delete_notification(db, notification_id)
    return {"ok": True}


@router.get("/unread/count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Количество непрочитанных уведомлений"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return {"unread_count": count}


@router.post("/me/mark-all-read")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Пометить все уведомления как прочитанные"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "Все уведомления прочитаны"}