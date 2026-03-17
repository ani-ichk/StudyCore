from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class Book(Base):
    """Таблица книг библиотеки"""
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(20))
    quantity_total = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)

    # Связи
    loans = relationship("LibraryLoan", back_populates="book")


class LibraryLoan(Base):
    """Таблица выдачи книг"""
    __tablename__ = 'library_loans'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    issued_at = Column(DateTime, default=datetime.now)
    deadline = Column(DateTime, nullable=False)
    returned_at = Column(DateTime)

    # Связи
    book = relationship("Book", back_populates="loans")
    user = relationship("User", back_populates="library_loans")