from .generate_view import router as generate_router
from .scaning_view import router as scaning_router
from .history_view import router as history_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(generate_router)
router.include_router(scaning_router)
router.include_router(history_router)
