from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from schemas import QRCodeGenerateRequest, QRCodeResponse
from api.api_v1.qrcode.services.qr_generator_service import QRGeneratorService
from api.api_v1.auth.dependencies import get_current_user, require_roles
from models import User

router = APIRouter(prefix="/generate", tags=["qrcode-generation"])


@router.post("", response_model=QRCodeResponse)
async def generate_qrcode(
    request: QRCodeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Генерация QR-кода для текущего пользователя.
    """
    generator_service = QRGeneratorService(db)
    
    try:
        qr_data = generator_service.generate_qr_code(
            user_id=current_user.id,
            purpose=request.purpose.value
        )
        
        return QRCodeResponse(
            id=qr_data['id'],
            code=qr_data['code'],
            image_base64=qr_data['image_base64'],
            expires_at=qr_data['expires_at'],
            purpose=request.purpose.value
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации QR-кода: {str(e)}"
        )


@router.post("/for-user/{user_id}", response_model=QRCodeResponse)
async def generate_qrcode_for_user(
    user_id: int,
    request: QRCodeGenerateRequest,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """
    Генерация QR-кода для другого пользователя (для администраторов и учителей).
    """
    generator_service = QRGeneratorService(db)
    
    try:
        qr_data = generator_service.generate_qr_code(
            user_id=user_id,
            purpose=request.purpose.value
        )
        
        return QRCodeResponse(
            id=qr_data['id'],
            code=qr_data['code'],
            image_base64=qr_data['image_base64'],
            expires_at=qr_data['expires_at'],
            purpose=request.purpose.value
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/active", response_model=List[QRCodeResponse])
async def get_active_qrcodes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение всех активных QR-кодов пользователя.
    """
    generator_service = QRGeneratorService(db)
    
    try:
        active_qrs = generator_service.get_active_qr_codes(current_user.id)
        return [
            QRCodeResponse(
                id=qr['id'],
                code=qr['code'],
                image_base64=qr['image_base64'],
                expires_at=qr['expires_at'],
                purpose="attendance"
            )
            for qr in active_qrs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении QR-кодов: {str(e)}"
        )


@router.post("/{qr_id}/invalidate")
async def invalidate_qrcode(
    qr_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Аннулирование QR-кода.
    """
    generator_service = QRGeneratorService(db)
    
    # Проверяем, принадлежит ли QR-код пользователю
    if not generator_service.validate_qr_ownership(qr_id, current_user.id):
        # Проверяем, может быть пользователь администратор
        if "admin" not in [role.name for role in current_user.roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав для аннулирования этого QR-кода"
            )
    
    success = generator_service.invalidate_qr_code(qr_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR-код не найден"
        )
    
    return {"message": "QR-код успешно аннулирован"}