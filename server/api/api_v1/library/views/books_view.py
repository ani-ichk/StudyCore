from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core import get_db
from models import Book, LibraryLoan
from schemas import BookCreate, BookOut
from api.api_v1.auth.dependencies import require_roles

router = APIRouter(prefix="/books", tags=["library-books"])

@router.post("", response_model=BookOut)
async def create_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "staff"]))
):
    new_book = Book(
        title=book_data.title,
        author=book_data.author,
        isbn=book_data.isbn,
        quantity_total=book_data.quantity_total,
        quantity_available=book_data.quantity_total
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@router.get("", response_model=List[BookOut])
async def get_books(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return db.query(Book).offset(skip).limit(limit).all()

@router.get("/{book_id}", response_model=BookOut)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book

@router.put("/{book_id}", response_model=BookOut)
async def update_book(
    book_id: int,
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "staff"]))
):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    book.title = book_data.title
    book.author = book_data.author
    book.isbn = book_data.isbn
    book.quantity_total = book_data.quantity_total
    book.quantity_available = book_data.quantity_total
    db.commit()
    db.refresh(book)
    return book

@router.delete("/{book_id}")
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "staff"]))
):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    
    loands = db.query(LibraryLoan).filter(LibraryLoan.book_id == book_id).all()
    if loands:
        for loand in loands:
            db.delete(loand)

    db.delete(book)
    db.commit()
    return {"ok": True}
