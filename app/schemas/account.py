from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.account import AccountType

class AccountCreate(BaseModel):
    name: str
    company: Optional[str] = None
    account_type: AccountType
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    alt_phone: Optional[str] = None
    email: Optional[str] = None
    web_address: Optional[str] = None
    parent_account_id: Optional[int] = None
    notes: Optional[str] = None

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    account_type: Optional[AccountType] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    alt_phone: Optional[str] = None
    email: Optional[str] = None
    web_address: Optional[str] = None
    parent_account_id: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class AccountResponse(BaseModel):
    id: int
    name: str
    company: Optional[str] = None
    account_type: AccountType
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    alt_phone: Optional[str] = None
    email: Optional[str] = None
    web_address: Optional[str] = None
    parent_account_id: Optional[int] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int