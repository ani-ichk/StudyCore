from fastapi import APIRouter
from .books_view import router as books_router
from .loans_view import router as loans_router

router = APIRouter()
router.include_router(books_router)
router.include_router(loans_router)
