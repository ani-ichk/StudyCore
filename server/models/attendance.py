from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from .base import Base
from .enums import EventType


class AttendanceLog(Base):
    """Таблица журнала посещаемости"""
    __tablename__ = 'attendance_log'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    # Связи
    user = relationship("User", back_populates="attendance_logs")