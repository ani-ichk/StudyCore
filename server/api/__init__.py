from fastapi import APIRouter

from .access_system.auth import router as auth_router

# Основной роутер API
router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
