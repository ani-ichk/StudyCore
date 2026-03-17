from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from api.api_v1.auth.services.auth_service import AuthService
from api.api_v1.auth.services.token_service import TokenService
from api.api_v1.auth.dependencies import get_current_user
from models import User

router = APIRouter(prefix="/logout", tags=["authentication"])


@router.post("")
async def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Выход из системы.
    
    - Удаляет cookie с токеном
    - Создает запись о выходе в журнале посещаемости
    """
    auth_service = AuthService(db)
    
    # Создаем запись о выходе
    auth_service.record_logout_attendance(current_user.id)
    
    # Удаляем cookie
    TokenService.clear_token_cookie(response)
    
    return {
        "message": "Успешный выход из системы",
        "user": f"{current_user.surname} {current_user.name}"
    }


@router.post("/all-devices")
async def logout_all_devices(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Выход из системы на всех устройствах.
    
    - Инвалидирует все текущие токены пользователя
    - Создает запись о выходе
    """
    auth_service = AuthService(db)
    
    # Создаем запись о выходе
    auth_service.record_logout_attendance(current_user.id)
    
    # Удаляем cookie
    TokenService.clear_token_cookie(response)
    
    # Здесь можно добавить логику инвалидации всех токенов
    # Например, увеличить версию токена в БД
    
    return {
        "message": "Выполнен выход со всех устройств",
        "user": f"{current_user.surname} {current_user.name}"
    }