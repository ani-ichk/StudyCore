from fastapi import APIRouter
from .notifications_view import router as notifications_router

router = APIRouter()
router.include_router(notifications_router)