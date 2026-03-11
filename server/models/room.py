from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from server.models.base import Base
from server.models.enums import RoomType


class Room(Base):
    """Таблица помещений"""
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)
    number = Column(String(20), nullable=False)
    description = Column(Enum(RoomType), default=RoomType.CLASSROOM)

    # Связи
    classes = relationship("Class", back_populates="classroom")
    keys = relationship("Key", back_populates="room")
    schedule_entries = relationship("Schedule", back_populates="classroom")