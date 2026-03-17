from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class QRCode(Base):
    """Таблица QR-кодов для пользователей"""
    __tablename__ = 'qr_codes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    code = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime)

    # Связи
    user = relationship("User", back_populates="qr_codes")