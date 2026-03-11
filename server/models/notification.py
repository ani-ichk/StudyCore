from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from server.models.base import Base
from server.models.enums import NotificationType


class Notification(Base):
    """Таблица уведомлений"""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    user = relationship("User", back_populates="notifications")