from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .enums import QRCodePurpose, EventType


class QRCodeGenerateRequest(BaseModel):
    purpose: QRCodePurpose = QRCodePurpose.ATTENDANCE


class QRCodeResponse(BaseModel):
    id: int
    code: str
    image_base64: str
    expires_at: datetime
    purpose: str


class QRCodeScanRequest(BaseModel):
    qr_data: str
    purpose: Optional[QRCodePurpose] = None


class AttendanceEventResponse(BaseModel):
    user_id: int
    user_name: str
    event_type: EventType
    timestamp: datetime
    purpose: str


class AttendanceHistoryItem(BaseModel):
    id: int
    event_type: str
    timestamp: datetime