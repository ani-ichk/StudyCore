from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

class LoanCreate(BaseModel):
    book_id: int
    user_id: int
    deadline: Optional[datetime] = None

class LoanOut(LoanCreate):
    id: int
    issued_at: datetime
    returned_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReturnBook(BaseModel):
    book_id: int
    user_id: int
