from .login_view import router as login_router
from .logout_view import router as logout_router
from .session_view import router as session_router
from .register_view import router as register_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(session_router)
router.include_router(register_router)