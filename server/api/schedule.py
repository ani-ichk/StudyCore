from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ...database import get_db
from ...schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from ...crud.schedule import (
    create_schedule, get_schedule, update_schedule, delete_schedule,
    get_schedules_by_class, get_schedules_by_teacher, get_schedules_by_room,
    check_schedule_conflicts
)

router = APIRouter(prefix="/schedule", tags=["Расписание"])


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_new_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """Создать урок с проверкой конфликтов"""
    conflicts = check_schedule_conflicts(db, schedule)
    if conflicts:
        raise HTTPException(
            status_code=400,
            detail={"message": "Конфликт расписания", "conflicts": conflicts}
        )
    return create_schedule(db, schedule)


@router.get("/class/{class_id}", response_model=List[ScheduleResponse])
def read_class_schedule(class_id: int, day_of_week: Optional[int] = None, db: Session = Depends(get_db)):
    """Расписание класса"""
    return get_schedules_by_class(db, class_id, day_of_week)


@router.get("/teacher/{teacher_id}", response_model=List[ScheduleResponse])
def read_teacher_schedule(teacher_id: int, day_of_week: Optional[int] = None, db: Session = Depends(get_db)):
    """Расписание учителя"""
    return get_schedules_by_teacher(db, teacher_id, day_of_week)


@router.get("/room/{classroom_id}", response_model=List[ScheduleResponse])
def read_room_schedule(classroom_id: int, day_of_week: Optional[int] = None, db: Session = Depends(get_db)):
    """Расписание по кабинету"""
    return get_schedules_by_room(db, classroom_id, day_of_week)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def read_one_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Урок не найден")
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_existing_schedule(schedule_id: int, schedule_update: ScheduleUpdate, db: Session = Depends(get_db)):
    db_schedule = get_schedule(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Урок не найден")

    conflicts = check_schedule_conflicts(db, schedule_update, exclude_id=schedule_id)  # Нужно адаптировать check под Update
    if conflicts:
        raise HTTPException(status_code=400, detail={"message": "Конфликт", "conflicts": conflicts})

    updated = update_schedule(db, schedule_id, schedule_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Не удалось обновить")
    return updated


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_schedule(schedule_id: int, db: Session = Depends(get_db)):
    if not delete_schedule(db, schedule_id):
        raise HTTPException(status_code=404, detail="Урок не найден")
    return None
