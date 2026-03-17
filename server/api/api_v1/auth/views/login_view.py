from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from core.database import get_db
from schemas import UserLogin, TokenResponse
from api.api_v1.auth.services.auth_service import AuthService
from api.api_v1.auth.services.token_service import TokenService

router = APIRouter(prefix="/login", tags=["authentication"])


@router.post("", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Вход в систему.
    
    - Проверяет логин и пароль
    - Возвращает JWT токен
    - Устанавливает cookie с токеном
    - Создает запись о входе в журнал посещаемости
    """
    # Инициализируем сервисы
    auth_service = AuthService(db)
    
    # Аутентификация пользователя
    user = auth_service.authenticate(login_data.login, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем, активен ли пользователь
    is_active, error_message = auth_service.validate_user_active(user)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message
        )
    
    # Создаем payload для токена
    token_payload = TokenService.create_user_token_payload(user)
    
    # Создаем access токен
    access_token = TokenService.create_access_token(token_payload)
    
    # Создаем refresh токен (опционально)
    refresh_token = TokenService.create_refresh_token(user.id)
    
    # Устанавливаем cookie с токеном
    TokenService.set_token_cookie(response, access_token)
    
    # Записываем событие входа в журнал
    auth_service.record_login_attendance(user.id)
    
    # Обновляем время последнего входа
    auth_service.update_last_login(user.id)
    
    # Формируем ответ с данными пользователя
    user_response = auth_service.create_user_response(user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Опционально
        token_type="bearer",
        user=user_response
    )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Обновление access токена с помощью refresh токена.
    """
    try:
        new_access_token = TokenService.refresh_access_token(refresh_token)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 60 * 60  # 1 час
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении токена: {str(e)}"
        )


@router.post("/check")
async def check_login(
    login: str,
    db: Session = Depends(get_db)
):
    """
    Проверка существования логина (для валидации на клиенте).
    """
    auth_service = AuthService(db)
    exists = auth_service.check_user_exists(login)
    
    return {
        "login": login,
        "exists": exists,
        "available": not exists
    }