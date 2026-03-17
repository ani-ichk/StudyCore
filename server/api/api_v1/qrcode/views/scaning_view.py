from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from schemas import (
    QRCodeScanRequest, AttendanceEventResponse, 
    EventType, QRCodePurpose
)
from api.api_v1.qrcode.services.qr_scanner_service import QRScannerService
from api.api_v1.qrcode.services.attendance_service import AttendanceService
from api.api_v1.auth.dependencies import require_roles, get_permission_checker
from models import User

router = APIRouter(prefix="/scan", tags=["qrcode-scanning"])


@router.post("", response_model=AttendanceEventResponse)
async def scan_qrcode(
    request: QRCodeScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher", "staff"]))
):
    """
    Сканирование QR-кода (текстовые данные).
    """
    # Инициализируем сервисы
    scanner_service = QRScannerService(db)
    attendance_service = AttendanceService(db)
    
    # Сканируем QR-код
    scan_result = scanner_service.scan_qr_text(
        request.qr_data, 
        request.purpose.value if request.purpose else None
    )
    
    user = scan_result['user']
    
    # Определяем тип события
    event_type_schema, _ = attendance_service.determine_event_type(user.id)
    
    # Создаем событие
    attendance_log = attendance_service.create_attendance_event(user.id)
    
    return AttendanceEventResponse(
        user_id=user.id,
        user_name=f"{user.surname} {user.name} {user.patronymic or ''}".strip(),
        event_type=event_type_schema,
        timestamp=attendance_log.timestamp,
        purpose=scan_result.get('purpose', 'attendance')
    )


@router.post("/image", response_model=AttendanceEventResponse)
async def scan_qrcode_image(
    file: UploadFile = File(...),
    purpose: Optional[QRCodePurpose] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher", "staff"]))
):
    """
    Сканирование QR-кода из загруженного изображения.
    """
    # Инициализируем сервисы
    scanner_service = QRScannerService(db)
    attendance_service = AttendanceService(db)
    
    # Проверяем формат файла
    if not scanner_service.validate_image_format(file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением"
        )
    
    # Читаем содержимое файла
    contents = await file.read()
    
    # Проверяем размер
    if not scanner_service.validate_image_size(contents):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Размер файла не должен превышать 10MB"
        )
    
    # Сканируем QR-код из изображения
    scan_result = scanner_service.scan_qr_image(
        contents,
        purpose.value if purpose else None
    )
    
    user = scan_result['user']
    
    # Определяем тип события
    event_type_schema, _ = attendance_service.determine_event_type(user.id)
    
    # Создаем событие
    attendance_log = attendance_service.create_attendance_event(user.id)
    
    return AttendanceEventResponse(
        user_id=user.id,
        user_name=f"{user.surname} {user.name} {user.patronymic or ''}".strip(),
        event_type=event_type_schema,
        timestamp=attendance_log.timestamp,
        purpose=scan_result.get('purpose', 'attendance')
    )


@router.post("/manual")
async def create_manual_attendance(
    user_id: int,
    event_type: EventType,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher"]))
):
    """
    Ручное создание записи посещаемости.
    """
    attendance_service = AttendanceService(db)
    
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    attendance_log = attendance_service.create_manual_event(user_id, event_type)
    
    return {
        "message": "Запись создана",
        "user": f"{user.surname} {user.name}",
        "event_type": event_type,
        "timestamp": attendance_log.timestamp
    }


@router.get("/status/{user_id}")
async def get_user_current_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "teacher", "parent"])),
    perm_checker = Depends(get_permission_checker)
):
    """
    Получение текущего статуса пользователя.
    """
    # Проверяем права доступа
    if not perm_checker.can_access_user_data(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данным этого пользователя"
        )
    
    attendance_service = AttendanceService(db)
    return attendance_service.get_user_status(user_id)