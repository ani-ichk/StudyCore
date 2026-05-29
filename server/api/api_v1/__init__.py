from fastapi import APIRouter
from .auth import router as auth_router
from .qrcode import router as qrcode_router
from .keysys import router as keysys_router
from .library import router as library_router
from .schedule import router as schedule_router
from .notifications import router as notifications_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(qrcode_router)
router.include_router(keysys_router)
router.include_router(library_router)
router.include_router(schedule_router)
router.include_router(notifications_router)