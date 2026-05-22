from fastapi import APIRouter
from .schedule_sys import router as schedule_router

router = APIRouter()
router.include_router(schedule_router)