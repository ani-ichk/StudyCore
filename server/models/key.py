from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Key(Base):
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True)  # K-101
    room = Column(String, index=True)  # 101, LIB, DIR
    status = Column(String, default="available")  # available, issued
    description = Column(String)

    #Связь с историей
    history = relationship("KeyIssue", back_populates="key")

class KeyIssue(Base):
    __tablename__ = "key_issues"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(Integer, ForeignKey("keys.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    issue_time = Column(DateTime, default=datetime.now)
    return_time = Column(DateTime, nullable=True)

    #Связи
    key = relationship("Key", back_populates="history")
    user = relationship("User")