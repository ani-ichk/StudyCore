from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from core import get_db
from models import Book, LibraryLoan, User
from schemas import LoanCreate, LoanOut, ReturnBook
from api.api_v1.auth.dependencies import require_roles, get_current_user, get_permission_checker

router = APIRouter(prefix="/loans", tags=["library-loans"])

@router.post("", response_model=LoanOut)
async def issue_book(
    loan_data: LoanCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "staff", "teacher"]))
):
    book = db.get(Book, loan_data.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    if book.quantity_available < 1:
        raise HTTPException(status_code=400, detail="Книга недоступна")
    user = db.get(User, loan_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    book.quantity_available -= 1
    deadline = loan_data.deadline or (datetime.now() + timedelta(days=14))
    new_loan = LibraryLoan(
        book_id=loan_data.book_id,
        user_id=loan_data.user_id,
        issued_at=datetime.now(),
        deadline=deadline
    )
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    return new_loan

@router.post("/return", response_model=LoanOut)
async def return_book(
    return_data: ReturnBook,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "staff", "teacher"]))
):
    loan = db.query(LibraryLoan).filter(
        LibraryLoan.book_id == return_data.book_id,
        LibraryLoan.user_id == return_data.user_id,
        LibraryLoan.returned_at.is_(None)
    ).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Активная выдача не найдена")
    
    loan.returned_at = datetime.now()
    book = db.get(Book, return_data.book_id)
    if book:
        book.quantity_available += 1
    db.commit()
    db.refresh(loan)
    return loan

@router.get("/user/{user_id}", response_model=List[LoanOut])
async def get_user_loans(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    perm_checker = Depends(get_permission_checker)
):
    if not perm_checker.can_access_user_data(current_user, user_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    return db.query(LibraryLoan).filter(LibraryLoan.user_id == user_id).all()

@router.get("/active", response_model=List[LoanOut])
async def get_active_loans(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "staff"]))
):
    return db.query(LibraryLoan).filter(LibraryLoan.returned_at.is_(None)).all()

@router.get("/overdue", response_model=List[LoanOut])
async def get_overdue_loans(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "staff"]))
):
    now = datetime.now()
    return db.query(LibraryLoan).filter(
        LibraryLoan.deadline < now,
        LibraryLoan.returned_at.is_(None)
    ).all()
