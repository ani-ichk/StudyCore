from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class KeyBase(BaseModel):
    number: str
    room_id: int
    description: Optional[str] = None


class KeyCreate(KeyBase):
    pass


class KeyUpdate(BaseModel):
    status: str
    description: Optional[str] = None


class KeyOut(KeyBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class KeyListOut(BaseModel):
    id: int
    number: str
    room_id: int
    status: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class KeyActionBase(BaseModel):
    action_type: str  # issue, return, report_lost, maintenance_start, maintenance_end
    description: Optional[str] = None


class KeyActionCreate(KeyActionBase):
    key_id: int
    user_id: int


class KeyActionOut(KeyActionBase):
    id: int
    key_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class KeyLogBase(BaseModel):
    key_id: int
    user_id: int


class KeyLogCreate(KeyLogBase):
    pass


class KeyLogOut(KeyLogBase):
    id: int
    issued_at: datetime
    returned_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KeyHistoryOut(BaseModel):
    id: int
    key_id: int
    key_number: str
    user_id: int
    user_name: str
    action_type: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True