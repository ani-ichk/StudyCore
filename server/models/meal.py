from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from server.models.base import Base
from server.models.enums import TransactionType


class MealAccount(Base):
    """Таблица счетов для питания"""
    __tablename__ = 'meal_accounts'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), unique=True, nullable=False)
    balance = Column(Float, default=0.0)

    # Связи
    student = relationship("Student", back_populates="meal_account")
    transactions = relationship("MealTransaction", back_populates="account")


class MealTransaction(Base):
    """Таблица транзакций по питанию"""
    __tablename__ = 'meal_transactions'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('meal_accounts.id'), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    description = Column(String(255))

    # Связи
    account = relationship("MealAccount", back_populates="transactions")