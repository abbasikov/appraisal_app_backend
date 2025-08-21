from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.APPRAISER
    license_number: Optional[str] = None
    certification_level: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    certification_level: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class EmailVerification(BaseModel):
    email: EmailStr
    code: str

class ResendVerification(BaseModel):
    email: EmailStr

class VerificationStatus(BaseModel):
    exists: bool
    is_verified: Optional[bool] = None
    has_pending_code: Optional[bool] = None
    code_expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    can_resend: Optional[bool] = None
    wait_time: Optional[int] = None