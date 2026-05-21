from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BookCreate(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    quantity_total: int = 1

class BookOut(BookCreate):
    id: int
    quantity_available: int
    class Config:
        from_attributes = True

class LoanCreate(BaseModel):
    book_id: int
    user_id: int
    deadline: Optional[datetime] = None

class LoanOut(LoanCreate):
    id: int
    issued_at: datetime
    returned_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ReturnBook(BaseModel):
    book_id: int
    user_id: int
