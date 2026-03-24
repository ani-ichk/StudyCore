from pydantic import BaseModel
from typing import Optional
from .user import UserResponse


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    user_id: int
    new_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str