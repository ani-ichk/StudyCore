from pydantic import BaseModel, ConfigDict, Field
from datetime import time, datetime
from typing import Optional


class ScheduleBase(BaseModel):
    class_id: int
    subject_id: int
    teacher_id: int
    classroom_id: int
    day_of_week: int = Field(..., ge=1, le=7)
    lesson_number: int = Field(..., ge=1)
    start_time: time
    end_time: time


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(ScheduleBase):
    class_id: Optional[int] = None
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    classroom_id: Optional[int] = None
    day_of_week: Optional[int] = Field(None, ge=1, le=7)
    lesson_number: Optional[int] = Field(None, ge=1)
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class ScheduleResponse(ScheduleBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)