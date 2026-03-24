import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from models import QRCode, User
from scripts.qrcode import QRCodeService


class QRGeneratorService:
    """Сервис для генерации QR-кодов."""
    
    def __init__(self, db: Session):
        self.db = db
        self.qr_service = QRCodeService()
    
    def generate_qr_code(
        self, 
        user_id: int, 
        purpose: str = "attendance",
        expiration_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Генерация нового QR-кода для пользователя.
        
        Args:
            user_id: ID пользователя
            purpose: Назначение QR-кода
            expiration_minutes: Время жизни в минутах
            
        Returns:
            Словарь с данными QR-кода
            
        Raises:
            ValueError: Если пользователь не найден
        """
        # Проверяем существование пользователя
        user = self.db.query(User).get(user_id)
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")
        
        # Деактивируем предыдущие активные QR-коды пользователя
        self._deactivate_previous_qrs(user_id)
        
        # Генерируем данные для QR-кода
        qr_data = self.qr_service.generate_qr_data(user_id, purpose)
        
        # Создаем запись в БД
        qr_record = QRCode(
            user_id=user_id,
            code=qr_data,
            expires_at=datetime.now() + timedelta(minutes=expiration_minutes)
        )
        
        self.db.add(qr_record)
        self.db.commit()
        self.db.refresh(qr_record)
        
        # Генерируем изображение
        img_bytes = self.qr_service.generate_qr_code_image(qr_data)
        img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
        
        return {
            'id': qr_record.id,
            'user_id': user_id,
            'user_name': f"{user.surname} {user.name}",
            'code': qr_data,
            'image_base64': img_base64,
            'expires_at': qr_record.expires_at.isoformat(),
            'purpose': purpose,
            'created_at': datetime.now().isoformat()
        }
    
    def _deactivate_previous_qrs(self, user_id: int) -> None:
        """
        Деактивация предыдущих активных QR-кодов пользователя.
        
        Args:
            user_id: ID пользователя
        """
        active_qrs = self.db.query(QRCode).filter(
            QRCode.user_id == user_id,
            QRCode.expires_at > datetime.now()
        ).all()
        
        for qr in active_qrs:
            qr.expires_at = datetime.now() - timedelta(minutes=1)
        
        if active_qrs:
            self.db.commit()
    
    def get_active_qr_codes(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получение всех активных QR-кодов пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список активных QR-кодов с изображениями
        """
        now = datetime.now()
        qr_codes = self.db.query(QRCode).filter(
            QRCode.user_id == user_id,
            QRCode.expires_at > now
        ).all()
        
        result = []
        for qr in qr_codes:
            img_bytes = self.qr_service.generate_qr_code_image(qr.code)
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            
            result.append({
                'id': qr.id,
                'code': qr.code,
                'image_base64': img_base64,
                'expires_at': qr.expires_at.isoformat() if qr.expires_at else None,
                'time_left': (qr.expires_at - now).seconds // 60 if qr.expires_at else 0
            })
        
        return result
    
    def invalidate_qr_code(self, qr_id: int) -> bool:
        """
        Аннулирование QR-кода.
        
        Args:
            qr_id: ID QR-кода
            
        Returns:
            True если успешно, False если QR-код не найден
        """
        qr_record = self.db.query(QRCode).get(qr_id)
        if qr_record:
            qr_record.expires_at = datetime.now() - timedelta(minutes=1)
            self.db.commit()
            return True
        return False
    
    def get_qr_code_by_id(self, qr_id: int) -> Optional[QRCode]:
        """
        Получение QR-кода по ID.
        
        Args:
            qr_id: ID QR-кода
            
        Returns:
            Объект QRCode или None
        """
        return self.db.query(QRCode).get(qr_id)
    
    def validate_qr_ownership(self, qr_id: int, user_id: int) -> bool:
        """
        Проверка, принадлежит ли QR-код пользователю.
        
        Args:
            qr_id: ID QR-кода
            user_id: ID пользователя
            
        Returns:
            True если принадлежит
        """
        qr = self.get_qr_code_by_id(qr_id)
        return qr is not None and qr.user_id == user_id