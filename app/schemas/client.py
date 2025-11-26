from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class ClientCreate(BaseModel):
    name: str
    parent_account_id: Optional[int] = None  # Link to Account (attorney, estate planner, etc.)
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None  
    state: Optional[str] = None
    zip_code: Optional[str] = None
    # Divorce-specific fields
    attorney_name: Optional[str] = None
    attorney_email: Optional[str] = None
    attorney_phone: Optional[str] = None
    case_name: Optional[str] = None
    case_number: Optional[str] = None
    date_of_death: Optional[datetime] = None  # For estate cases later
    notes: Optional[str] = None
    
    @validator('email', 'attorney_email', pre=True)
    def validate_email(cls, v):
        if v and v.strip():
            # Basic email validation
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('Invalid email format')
            return v.strip()
        return None

class ClientUpdate(ClientCreate):
    pass

class ClientResponse(BaseModel):
    id: int
    name: str
    parent_account_id: Optional[int] = None
    parent_account_name: Optional[str] = None  # From joined account table
    parent_account_address: Optional[str] = None  # From parent account
    parent_account_city: Optional[str] = None  # From parent account
    parent_account_state: Optional[str] = None  # From parent account
    parent_account_zip: Optional[str] = None  # From parent account
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