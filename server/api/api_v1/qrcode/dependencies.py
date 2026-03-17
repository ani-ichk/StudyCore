from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from api.api_v1.qrcode.services import (
    QRGeneratorService,
    QRScannerService,
    AttendanceService,
    HistoryService
)


def get_qr_generator_service(db: Session = Depends(get_db)) -> QRGeneratorService:
    """Получение сервиса генерации QR-кодов."""
    return QRGeneratorService(db)


def get_qr_scanner_service(db: Session = Depends(get_db)) -> QRScannerService:
    """Получение сервиса сканирования QR-кодов."""
    return QRScannerService(db)


def get_attendance_service(db: Session = Depends(get_db)) -> AttendanceService:
    """Получение сервиса посещаемости."""
    return AttendanceService(db)


def get_history_service(db: Session = Depends(get_db)) -> HistoryService:
    """Получение сервиса истории."""
    return HistoryService(db)