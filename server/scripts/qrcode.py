import qrcode
from io import BytesIO
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from models import QRCode, User, AttendanceLog
from models.enums import EventType


class QRCodeService:
    """Сервис для работы с QR-кодами"""

    @staticmethod
    def generate_qr_data(user_id: int, purpose: str = "attendance") -> str:
        """
        Генерация данных для QR-кода с улучшенной структурой
        Формат: school:user_id:purpose:timestamp:token:version
        """
        token = secrets.token_urlsafe(16)
        timestamp = int(datetime.now().timestamp())
        version = "1.0"
        
        qr_data = f"school:{user_id}:{purpose}:{timestamp}:{token}:{version}"
        return qr_data

    @staticmethod
    def generate_qr_code_image(data: str, size: int = 10, border: int = 4) -> BytesIO:
        """Генерация изображения QR-кода"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes

    @staticmethod
    def generate_qr_code_base64(data: str, size: int = 10) -> str:
        """Генерация QR-кода в формате base64"""
        img_bytes = QRCodeService.generate_qr_code_image(data, size)
        return base64.b64encode(img_bytes.getvalue()).decode('utf-8')

    @staticmethod
    def parse_qr_data(qr_data: str) -> Optional[dict]:
        """Парсинг данных из QR-кода с поддержкой разных версий"""
        try:
            parts = qr_data.split(':')
            
            # Проверяем минимальную длину и префикс
            if len(parts) < 5 or parts[0] != 'school':
                return None
            
            # Определяем версию формата
            version = parts[5] if len(parts) > 5 else "1.0"
            
            result = {
                'user_id': int(parts[1]),
                'purpose': parts[2],
                'timestamp': int(parts[3]),
                'token': parts[4],
                'version': version,
                'is_expired': QRCodeService.is_qr_expired(int(parts[3]))
            }
            
            return result
        except (ValueError, IndexError) as e:
            print(f"Ошибка парсинга QR-кода: {e}")
            return None

    @staticmethod
    def is_qr_expired(timestamp: int, expiration_minutes: int = 5) -> bool:
        """Проверка истечения срока действия QR-кода"""
        qr_time = datetime.fromtimestamp(timestamp)
        current_time = datetime.now()
        expiration_time = qr_time + timedelta(minutes=expiration_minutes)
        
        return current_time > expiration_time

    @staticmethod
    def validate_qr_code(qr_data: str, expected_purpose: str = None) -> Tuple[bool, dict]:
        """Валидация QR-кода с подробной информацией об ошибках"""
        data = QRCodeService.parse_qr_data(qr_data)
        if not data:
            return False, {'error': 'Неверный формат QR-кода'}

        if data['is_expired']:
            expired_minutes = (datetime.now() - datetime.fromtimestamp(data['timestamp'])).seconds // 60
            return False, {
                'error': 'QR-код просрочен',
                'expired_minutes': expired_minutes,
                'timestamp': data['timestamp']
            }

        if expected_purpose and data['purpose'] != expected_purpose:
            return False, {
                'error': f'Неверное назначение QR-кода. Ожидалось: {expected_purpose}, получено: {data["purpose"]}'
            }

        return True, data

    @staticmethod
    def decode_qr_from_image_bytes(image_bytes: bytes) -> Optional[str]:
        """Декодирование QR-кода из изображения"""
        if not OPENCV_AVAILABLE:
            raise ImportError('Для сканирования QR-кодов требуется OpenCV')
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None

            detector = cv2.QRCodeDetector()
            data, points, _ = detector.detectAndDecode(img)
            return data if data else None
        except Exception as e:
            print(f"Ошибка декодирования QR-кода: {e}")
            return None


class QRCodeGenerator:
    """Генератор QR-кодов для пользователей системы"""
    
    def __init__(self, db: Session):
        self.db = db

    def generate_user_qr_code(self, user_id: int, purpose: str = "attendance", 
                             expiration_minutes: int = 5) -> dict:
        """
        Генерация QR-кода для пользователя с сохранением в БД
        """
        # Проверяем существование пользователя
        user = self.db.query(User).get(user_id)
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")
        
        # Генерируем данные
        qr_data = QRCodeService.generate_qr_data(user_id, purpose)
        
        # Деактивируем предыдущие активные QR-коды пользователя
        active_qrs = self.db.query(QRCode).filter(
            QRCode.user_id == user_id,
            QRCode.expires_at > datetime.now()
        ).all()
        
        for qr in active_qrs:
            qr.expires_at = datetime.now() - timedelta(minutes=1)
        
        # Создаем новую запись
        qr_record = QRCode(
            user_id=user_id,
            code=qr_data,
            expires_at=datetime.now() + timedelta(minutes=expiration_minutes)
        )
        
        self.db.add(qr_record)
        self.db.commit()
        self.db.refresh(qr_record)
        
        # Генерируем изображение
        img_bytes = QRCodeService.generate_qr_code_image(qr_data)
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
    
    def get_user_attendance_status(self, user_id: int) -> dict:
        """
        Получение текущего статуса присутствия пользователя
        """
        last_event = self.db.query(AttendanceLog)\
            .filter_by(user_id=user_id)\
            .order_by(AttendanceLog.timestamp.desc())\
            .first()
        
        if not last_event:
            return {
                'user_id': user_id,
                'status': 'unknown',
                'last_event': None
            }
        
        return {
            'user_id': user_id,
            'status': 'inside' if last_event.event_type == EventType.IN else 'outside',
            'last_event': {
                'type': last_event.event_type.value,
                'timestamp': last_event.timestamp.isoformat()
            }
        }