from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from core.database import get_db
from schemas import AttendanceHistoryItem
from api.api_v1.qrcode.services.history_service import HistoryService
from api.api_v1.auth.dependencies import (
    require_roles, get_permission_checker, PermissionChecker
)
from models import User

router = APIRouter(prefix="/history", tags=["qrcode-history"])


@router.get("/user/{user_id}", response_model=List[AttendanceHistoryItem])
async def get_user_history(
    user_id: int,
    date_from: Optional[date] = Query(None, description="Начальная дата (ГГГГ-ММ-ДД)"),
    date_to: Optional[date] = Query(None, description="Конечная дата (ГГГГ-ММ-ДД)"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher", "parent", "student"])),
    perm_checker: PermissionChecker = Depends(get_permission_checker)
):
    """
    Получение истории посещений конкретного пользователя.
    """
    # Проверяем права доступа
    if not perm_checker.can_access_user_data(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к истории этого пользователя"
        )
    
    history_service = HistoryService(db)
    
    events = history_service.get_user_history(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    
    return history_service.format_history_items(events)


@router.get("/me", response_model=List[AttendanceHistoryItem])
async def get_my_history(
    date_from: Optional[date] = Query(None, description="Начальная дата (ГГГГ-ММ-ДД)"),
    date_to: Optional[date] = Query(None, description="Конечная дата (ГГГГ-ММ-ДД)"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student", "teacher", "parent"]))
):
    """
    Получение своей истории посещений.
    """
    history_service = HistoryService(db)
    
    events = history_service.get_user_history(
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    
    return history_service.format_history_items(events)


@router.get("/summary/{user_id}")
async def get_attendance_summary(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher", "parent"])),
    perm_checker: PermissionChecker = Depends(get_permission_checker)
):
    """
    Получение сводной статистики по посещаемости.
    """
    # Проверяем права
    if not perm_checker.can_access_user_data(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данным этого пользователя"
        )
    
    history_service = HistoryService(db)
    return history_service.get_attendance_summary(user_id, days)


@router.get("/range")
async def get_history_by_date_range(
    date_from: date = Query(..., description="Начальная дата (ГГГГ-ММ-ДД)"),
    date_to: date = Query(..., description="Конечная дата (ГГГГ-ММ-ДД)"),
    user_id: Optional[int] = Query(None, description="ID пользователя для фильтрации"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"]))
):
    """
    Получение истории посещений за диапазон дат.
    """
    history_service = HistoryService(db)
    return history_service.get_range_history(date_from, date_to, user_id)


@router.get("/count/{user_id}")
async def get_user_history_count(
    user_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher", "parent"])),
    perm_checker: PermissionChecker = Depends(get_permission_checker)
):
    """
    Получение количества записей истории пользователя.
    """
    if not perm_checker.can_access_user_data(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данным этого пользователя"
        )
    
    history_service = HistoryService(db)
    count = history_service.get_user_history_count(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to
    )
    
    return {
        "user_id": user_id,
        "count": count,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None
    }