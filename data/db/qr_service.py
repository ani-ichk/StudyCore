import qrcode
from io import BytesIO
import base64
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
import uuid

try:
    import cv2
    import numpy as np

    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class QRCodeService:
    """Сервис для работы с QR-кодами"""

    @staticmethod
    def generate_qr_data(user_id: int, purpose: str = "attendance") -> str:
        """
        Генерация данных для QR-кода

        Args:
            user_id: ID пользователя
            purpose: Назначение QR-кода (attendance, library, meal, etc.)

        Returns:
            Строка с данными для QR-кода
        """
        # Создаем уникальный токен
        token = secrets.token_urlsafe(16)
        timestamp = int(datetime.now().timestamp())

        # Формат: school:user_id:purpose:timestamp:token
        qr_data = f"school:{user_id}:{purpose}:{timestamp}:{token}"

        return qr_data

    @staticmethod
    def generate_qr_code_image(data: str, size: int = 10, border: int = 4) -> BytesIO:
        """
        Генерация изображения QR-кода

        Args:
            data: Данные для кодирования
            size: Размер QR-кода (1-40)
            border: Толщина рамки

        Returns:
            BytesIO объект с PNG изображением
        """
        # Создаем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")

        # Сохраняем в BytesIO
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return img_bytes

    @staticmethod
    def generate_qr_code_base64(data: str, size: int = 10) -> str:
        """
        Генерация QR-кода в формате base64

        Returns:
            Base64 строка с изображением PNG
        """
        img_bytes = QRCodeService.generate_qr_code_image(data, size)
        return base64.b64encode(img_bytes.getvalue()).decode('utf-8')

    @staticmethod
    def parse_qr_data(qr_data: str) -> Optional[dict]:
        """
        Парсинг данных из QR-кода

        Returns:
            Словарь с распарсенными данными или None при ошибке
        """
        try:
            parts = qr_data.split(':')
            if len(parts) != 5 or parts[0] != 'school':
                return None

            return {
                'user_id': int(parts[1]),
                'purpose': parts[2],
                'timestamp': int(parts[3]),
                'token': parts[4],
                'is_expired': QRCodeService.is_qr_expired(int(parts[3]))
            }
        except (ValueError, IndexError):
            return None

    @staticmethod
    def is_qr_expired(timestamp: int, expiration_minutes: int = 5) -> bool:
        """
        Проверка истечения срока действия QR-кода

        Args:
            timestamp: Временная метка создания QR-кода
            expiration_minutes: Время жизни QR-кода в минутах

        Returns:
            True если QR-код просрочен
        """
        qr_time = datetime.fromtimestamp(timestamp)
        current_time = datetime.now()
        expiration_time = qr_time + timedelta(minutes=expiration_minutes)

        return current_time > expiration_time

    @staticmethod
    def validate_qr_code(qr_data: str, expected_purpose: str = None) -> Tuple[bool, dict]:
        """
        Валидация QR-кода

        Returns:
            Кортеж (is_valid, data_dict)
        """
        data = QRCodeService.parse_qr_data(qr_data)
        if not data:
            return False, {'error': 'Неверный формат QR-кода'}

        if data['is_expired']:
            return False, {'error': 'QR-код просрочен'}

        if expected_purpose and data['purpose'] != expected_purpose:
            return False, {'error': f'Неверное назначение QR-кода. Ожидалось: {expected_purpose}'}

        return True, data


class QRCodeGenerator:
    """Генератор QR-кодов для пользователей системы"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def generate_user_qr_code(self, user_id: int, purpose: str = "attendance") -> dict:
        """
        Генерация QR-кода для пользователя с сохранением в БД

        Returns:
            Словарь с данными QR-кода
        """
        from .models import QRCode

        session = self.db_manager.get_session()
        try:
            # Генерируем данные
            qr_data = QRCodeService.generate_qr_data(user_id, purpose)

            # Создаем запись в БД
            qr_record = QRCode(
                user_id=user_id,
                code=qr_data,
                expires_at=datetime.now() + timedelta(minutes=5)
            )

            session.add(qr_record)
            session.commit()
            session.refresh(qr_record)

            # Генерируем изображение
            img_bytes = QRCodeService.generate_qr_code_image(qr_data)
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

            return {
                'id': qr_record.id,
                'user_id': user_id,
                'code': qr_data,
                'image_base64': img_base64,
                'expires_at': qr_record.expires_at.isoformat(),
                'purpose': purpose
            }
        finally:
            session.close()

    def validate_qr_code(self, qr_code: str) -> dict:
        """
        Валидация QR-кода из БД

        Returns:
            Словарь с результатом валидации
        """
        from .models import QRCode, User

        session = self.db_manager.get_session()
        try:
            # Ищем QR-код в БД
            qr_record = session.query(QRCode).filter_by(code=qr_code).first()

            if not qr_record:
                return {
                    'valid': False,
                    'error': 'QR-код не найден'
                }

            # Проверяем срок действия
            if qr_record.expires_at and qr_record.expires_at < datetime.now():
                return {
                    'valid': False,
                    'error': 'QR-код просрочен',
                    'user_id': qr_record.user_id
                }

            # Получаем информацию о пользователе
            user = session.query(User).get(qr_record.user_id)

            return {
                'valid': True,
                'user_id': qr_record.user_id,
                'user_name': user.name if user else 'Неизвестный',
                'qr_id': qr_record.id,
                'expires_at': qr_record.expires_at.isoformat() if qr_record.expires_at else None
            }
        finally:
            session.close()

    def get_active_qr_codes(self, user_id: int) -> list:
        """Получить активные QR-коды пользователя"""
        from .models import QRCode

        session = self.db_manager.get_session()
        try:
            now = datetime.now()
            qr_codes = session.query(QRCode).filter(
                QRCode.user_id == user_id,
                QRCode.expires_at > now
            ).all()

            result = []
            for qr in qr_codes:
                img_bytes = QRCodeService.generate_qr_code_image(qr.code)
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

                result.append({
                    'id': qr.id,
                    'code': qr.code,
                    'image_base64': img_base64,
                    'expires_at': qr.expires_at.isoformat() if qr.expires_at else None
                })

            return result
        finally:
            session.close()

    def invalidate_qr_code(self, qr_id: int) -> bool:
        """Аннулировать QR-код"""
        from .models import QRCode

        session = self.db_manager.get_session()
        try:
            qr_record = session.query(QRCode).get(qr_id)
            if qr_record:
                qr_record.expires_at = datetime.now() - timedelta(minutes=1)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()