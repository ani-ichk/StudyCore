from pydantic import BaseModel, EmailStr
from typing import Optional, List
from .enums import UserRole


class UserBase(BaseModel):
    login: str
    surname: str
    name: str
    patronymic: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str
    role_names: List[str]


class UserResponse(UserBase):
    id: int
    is_active: bool
    roles: List[str]
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    login: str
    password: str