from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from fastapi import HTTPException, status, Response

from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models import User


class TokenService:
    """Сервис для работы с JWT токенами."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """
        Создание JWT токена с расширенными данными.
        
        Args:
            data: Данные для включения в токен
            
        Returns:
            JWT токен в виде строки
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            print(f"Ошибка при создании токена: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании токена"
            )
    
    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """
        Создание refresh токена для обновления access токена.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Refresh токен
        """
        expire = datetime.utcnow() + timedelta(days=30)  # Refresh токен живет 30 дней
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "refresh"
        }
        
        refresh_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return refresh_token
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Декодирование и валидация токена.
        
        Args:
            token: JWT токен
            
        Returns:
            Декодированные данные токена
            
        Raises:
            HTTPException: Если токен недействителен или истек
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен истек",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Недействительный токен: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Обновление access токена с помощью refresh токена.
        
        Args:
            refresh_token: Refresh токен
            
        Returns:
            Новый access токен
        """
        payload = TokenService.decode_token(refresh_token)
        
        # Проверяем тип токена
        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный тип токена",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный refresh токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Создаем новый access токен
        new_access_token = TokenService.create_access_token(
            data={"sub": user_id, "user_id": int(user_id)}
        )
        
        return new_access_token
    
    @staticmethod
    def set_token_cookie(response: Response, access_token: str) -> None:
        """
        Установка cookie с токеном.
        
        Args:
            response: FastAPI Response объект
            access_token: JWT токен
        """
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,  # В разработке можно False, в продакшне True
            samesite="lax",
            path="/"
        )
    
    @staticmethod
    def clear_token_cookie(response: Response) -> None:
        """
        Удаление cookie с токеном.
        
        Args:
            response: FastAPI Response объект
        """
        response.delete_cookie(
            key="access_token",
            path="/",
            samesite="lax"
        )
    
    @staticmethod
    def create_user_token_payload(user: User) -> Dict[str, Any]:
        """
        Создание payload для токена на основе данных пользователя.
        
        Args:
            user: Объект пользователя
            
        Returns:
            Словарь с данными для токена
        """
        return {
            "sub": user.login,
            "user_id": user.id,
            "roles": [role.name for role in user.roles],
            "name": f"{user.surname} {user.name}",
            "email": user.email
        }