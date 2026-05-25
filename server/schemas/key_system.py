from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class KeyBase(BaseModel):
    number: str
    room: str
    description: str

class KeyCreate(KeyBase):
    pass

class KeyOut(KeyBase):
    id: int
    status: str

    class Config:
        from_attributes = True

class KeyIssueOut(BaseModel):
    id: int
    key_id: int
    key_number: str
    user_id: int
    user_name: str
    issue_time: datetime
    return_time: Optional[datetime]

    class Config:
        from_attributes = True