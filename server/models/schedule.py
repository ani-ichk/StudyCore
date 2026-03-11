from sqlalchemy import Column, Integer, ForeignKey, Time
from sqlalchemy.orm import relationship
from server.models.base import Base


class Schedule(Base):
    """Таблица расписания"""
    __tablename__ = 'schedule'

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    classroom_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    day_of_week = Column(Integer, nullable=False)    # 1-понедельник, 7-воскресенье
    lesson_number = Column(Integer, nullable=False) # 1-й урок, 2-й и т.д.
    start_time = Column(Time)
    end_time = Column(Time)

    # Связи
    class_ = relationship("Class", back_populates="schedule_entries")
    subject = relationship("Subject", back_populates="schedule_entries")
    teacher = relationship("User", back_populates="schedule_entries")
    classroom = relationship("Room", back_populates="schedule_entries")