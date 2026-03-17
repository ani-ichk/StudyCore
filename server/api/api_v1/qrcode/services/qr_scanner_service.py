from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import base64

from models import User
from scripts.qrcode import QRCodeService


class QRScannerService:
    """Сервис для сканирования и валидации QR-кодов."""
    
    def __init__(self, db: Session):
        self.db = db
        self.qr_service = QRCodeService()
    
    def validate_qr_data(
        self, 
        qr_data: str, 
        expected_purpose: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Валидация данных QR-кода.
        
        Args:
            qr_data: Данные QR-кода
            expected_purpose: Ожидаемое назначение
            
        Returns:
            Кортеж (успех, данные или сообщение об ошибке)
        """
        return self.qr_service.validate_qr_code(qr_data, expected_purpose)
    
    def get_user_from_qr(self, qr_data: str) -> Optional[User]:
        """
        Получение пользователя из данных QR-кода.
        
        Args:
            qr_data: Данные QR-кода
            
        Returns:
            Объект пользователя или None
        """
        is_valid, data = self.validate_qr_data(qr_data)
        if not is_valid:
            return None
        
        user_id = data.get('user_id')
        if not user_id:
            return None
        
        return self.db.query(User).get(user_id)
    
    def scan_qr_text(self, qr_data: str, expected_purpose: Optional[str] = None) -> Dict[str, Any]:
        """
        Сканирование текстовых данных QR-кода.
        
        Args:
            qr_data: Данные QR-кода
            expected_purpose: Ожидаемое назначение
            
        Returns:
            Словарь с данными пользователя и QR-кода
            
        Raises:
            HTTPException: Если QR-код недействителен
        """
        # Валидация QR-кода
        is_valid, data = self.validate_qr_data(qr_data, expected_purpose)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=data.get('error', 'Недействительный QR-код')
            )
        
        user_id = data['user_id']
        
        # Проверяем пользователя
        user = self.db.query(User).get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь деактивирован"
            )
        
        return {
            'user': user,
            'qr_data': data,
            'user_id': user_id,
            'purpose': data.get('purpose', 'unknown')
        }
    
    def scan_qr_image(self, image_bytes: bytes, expected_purpose: Optional[str] = None) -> Dict[str, Any]:
        """
        Сканирование QR-кода из изображения.
        
        Args:
            image_bytes: Байты изображения
            expected_purpose: Ожидаемое назначение
            
        Returns:
            Словарь с данными пользователя и QR-кода
            
        Raises:
            HTTPException: Если QR-код не найден или недействителен
        """
        # Декодируем QR-код из изображения
        try:
            qr_data = self.qr_service.decode_qr_from_image_bytes(image_bytes)
            if not qr_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Не удалось найти QR-код на изображении"
                )
        except ImportError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        
        # Валидируем и возвращаем результат
        return self.scan_qr_text(qr_data, expected_purpose)
    
    def validate_image_format(self, content_type: str) -> bool:
        """
        Проверка формата изображения.
        
        Args:
            content_type: MIME тип изображения
            
        Returns:
            True если формат поддерживается
        """
        return content_type.startswith('image/')
    
    def validate_image_size(self, image_bytes: bytes, max_size_mb: int = 10) -> bool:
        """
        Проверка размера изображения.
        
        Args:
            image_bytes: Байты изображения
            max_size_mb: Максимальный размер в МБ
            
        Returns:
            True если размер допустим
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        return len(image_bytes) <= max_size_bytes