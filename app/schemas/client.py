from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ClientCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None  
    state: Optional[str] = None
    zip_code: Optional[str] = None
    # Divorce-specific fields
    attorney_name: Optional[str] = None
    attorney_email: Optional[EmailStr] = None
    attorney_phone: Optional[str] = None
    case_name: Optional[str] = None
    case_number: Optional[str] = None
    date_of_death: Optional[datetime] = None  # For estate cases later
    notes: Optional[str] = None

class ClientUpdate(ClientCreate):
    pass

class ClientResponse(BaseModel):
    id: int
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    attorney_name: Optional[str] = None
    attorney_email: Optional[str] = None
    attorney_phone: Optional[str] = None
    case_name: Optional[str] = None
    case_number: Optional[str] = None
    date_of_death: Optional[datetime] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True