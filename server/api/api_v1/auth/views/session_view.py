from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from schemas import UserResponse
from api.api_v1.auth.services.auth_service import AuthService
from api.api_v1.auth.services.token_service import TokenService
from api.api_v1.auth.dependencies import get_current_user
from models import User

router = APIRouter(prefix="/session", tags=["session"])


@router.get("/me", response_model=UserResponse)
async def get_current_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение информации о текущей сессии и пользователе.
    """
    auth_service = AuthService(db)
    return auth_service.create_user_response(current_user)


@router.get("/verify")
async def verify_session(
    current_user: User = Depends(get_current_user)
):
    """
    Проверка валидности текущей сессии.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "login": current_user.login,
        "roles": [role.name for role in current_user.roles],
        "expires_in": 60 * 60  # Информация о времени жизни токена
    }


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Смена пароля текущего пользователя.
    """
    from scripts.auth_methods import change_password
    
    success, message = change_password(db, current_user.id, old_password, new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@router.get("/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    Получение всех прав текущего пользователя на основе ролей.
    """
    user_roles = [role.name for role in current_user.roles]
    
    # Определяем права на основе ролей, можно дополнить
    permissions = {
        "can_view_users": "admin" in user_roles or "teacher" in user_roles,
        "can_edit_users": "admin" in user_roles,
        "can_view_grades": any(r in user_roles for r in ["admin", "teacher", "student", "parent"]),
        "can_edit_grades": "teacher" in user_roles or "admin" in user_roles,
        "can_scan_qrcode": any(r in user_roles for r in ["admin", "teacher", "staff"]),
        "can_generate_qrcode": any(r in user_roles for r in ["admin", "teacher", "student"]),
        "can_view_attendance": any(r in user_roles for r in ["admin", "teacher", "parent"]),
        "can_manage_keys": "admin" in user_roles or "staff" in user_roles,
        "can_manage_library": any(r in user_roles for r in ["admin", "staff"]),
        "can_view_meal_balance": any(r in user_roles for r in ["admin", "student", "parent"]),
    }
    
    return {
        "user_id": current_user.id,
        "roles": user_roles,
        "permissions": permissions
    }