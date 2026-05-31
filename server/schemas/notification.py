from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from models.enums import NotificationType


class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    message: str


class NotificationOut(NotificationCreate):
    id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUpdate(BaseModel):
    is_read: bool = True


class NotificationListOut(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)