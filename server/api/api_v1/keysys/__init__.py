from fastapi import APIRouter
from .key_system import router as keys_router

router = APIRouter()
router.include_router(keys_router)