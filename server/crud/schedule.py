from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.schedule import Schedule


def get_schedule(db: Session, schedule_id: int):
    return db.query(Schedule).filter(Schedule.id == schedule_id).first()


def get_schedules_by_class(db: Session, class_id: int, day_of_week: Optional[int] = None) -> List[Schedule]:
    query = db.query(Schedule).filter(Schedule.class_id == class_id)
    if day_of_week:
        query = query.filter(Schedule.day_of_week == day_of_week)
    return query.order_by(Schedule.day_of_week, Schedule.lesson_number).all()


def get_schedules_by_teacher(db: Session, teacher_id: int, day_of_week: Optional[int] = None) -> List[Schedule]:
    query = db.query(Schedule).filter(Schedule.teacher_id == teacher_id)
    if day_of_week:
        query = query.filter(Schedule.day_of_week == day_of_week)
    return query.order_by(Schedule.day_of_week, Schedule.lesson_number).all()


def get_schedules_by_room(db: Session, classroom_id: int, day_of_week: Optional[int] = None) -> List[Schedule]:
    query = db.query(Schedule).filter(Schedule.classroom_id == classroom_id)
    if day_of_week:
        query = query.filter(Schedule.day_of_week == day_of_week)
    return query.order_by(Schedule.day_of_week, Schedule.lesson_number).all()


def check_schedule_conflicts(db: Session, schedule: ScheduleCreate, exclude_id: Optional[int] = None) -> List[str]:
    """Проверка конфликтов: класс, учитель, кабинет"""
    conflicts = []
    base_filters = [
        Schedule.day_of_week == schedule.day_of_week,
        Schedule.lesson_number == schedule.lesson_number
    ]
    if exclude_id:
        base_filters.append(Schedule.id != exclude_id)

    # Конфликт класса
    if db.query(Schedule).filter(*base_filters, Schedule.class_id == schedule.class_id).first():
        conflicts.append("В этом классе уже есть урок в это время")

    # Конфликт учителя
    if db.query(Schedule).filter(*base_filters, Schedule.teacher_id == schedule.teacher_id).first():
        conflicts.append("Учитель уже ведёт урок в это время")

    # Конфликт кабинета
    if db.query(Schedule).filter(*base_filters, Schedule.classroom_id == schedule.classroom_id).first():
        conflicts.append("Кабинет уже занят в это время")

    return conflicts


def create_schedule(db: Session, schedule: ScheduleCreate) -> Schedule:
    conflicts = check_schedule_conflicts(db, schedule)
    if conflicts:
        raise ValueError(f"Конфликты: {conflicts}")

    db_schedule = Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def update_schedule(db: Session, schedule_id: int, schedule_update) -> Optional[Schedule]:
    db_schedule = get_schedule(db, schedule_id)
    if not db_schedule:
        return None

    for key, value in schedule_update.dict(exclude_unset=True).items():
        setattr(db_schedule, key, value)

    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def delete_schedule(db: Session, schedule_id: int) -> bool:
    db_schedule = get_schedule(db, schedule_id)
    if db_schedule:
        db.delete(db_schedule)
        db.commit()
        return True
    return False