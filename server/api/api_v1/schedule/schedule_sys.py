from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core import get_db
from schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from crud import (
    create_schedule, get_schedule, update_schedule, delete_schedule,
    get_schedules_by_class, get_schedules_by_teacher, get_schedules_by_room,
    check_schedule_conflicts
)

from api.api_v1.auth.dependencies import get_current_user, require_roles
from api.api_v1.auth.services.auth_service import User

router = APIRouter(prefix="/schedule", tags=["Расписание"])


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_new_schedule(
        schedule: ScheduleCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_roles(["admin", "завуч", "head_teacher"]))
):
    """Создать урок — только администрация и завуч"""

    conflicts = check_schedule_conflicts(db, schedule)
    if conflicts:
        raise HTTPException(
            status_code=400,
            detail={"message": "Конфликт расписания", "conflicts": conflicts}
        )

    return create_schedule(db, schedule)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_existing_schedule(
        schedule_id: int,
        schedule_update: ScheduleUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_roles(["admin", "завуч", "head_teacher"]))
):
    """Обновить урок"""
    db_schedule = get_schedule(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Урок не найден")

    conflicts = check_schedule_conflicts(db, schedule_update, exclude_id=schedule_id)
    if conflicts:
        raise HTTPException(
            status_code=400,
            detail={"message": "Конфликт расписания", "conflicts": conflicts}
        )

    updated = update_schedule(db, schedule_id, schedule_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Не удалось обновить")
    return updated


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_schedule(
        schedule_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_roles(["admin", "завуч"]))
):
    """Удалить урок — только админ и завуч"""
    if not delete_schedule(db, schedule_id):
        raise HTTPException(status_code=404, detail="Урок не найден")
    return None


@router.get("/class/{class_id}", response_model=List[ScheduleResponse])
def read_class_schedule(
        class_id: int,
        day_of_week: Optional[int] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Просмотр расписания класса"""
    return get_schedules_by_class(db, class_id, day_of_week)


@router.get("/teacher/{teacher_id}", response_model=List[ScheduleResponse])
def read_teacher_schedule(
        teacher_id: int,
        day_of_week: Optional[int] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Просмотр расписания учителя"""
    return get_schedules_by_teacher(db, teacher_id, day_of_week)


@router.get("/room/{classroom_id}", response_model=List[ScheduleResponse])
def read_room_schedule(
        classroom_id: int,
        day_of_week: Optional[int] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Просмотр расписания по кабинету"""
    return get_schedules_by_room(db, classroom_id, day_of_week)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def read_one_schedule(
        schedule_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Просмотр одного урока"""
    schedule = get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Урок не найден")
    return schedule
