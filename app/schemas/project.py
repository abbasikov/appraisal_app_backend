from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class AppraisalType(str, Enum):
    DIVORCE = "DIVORCE"
    ESTATE = "ESTATE" 
    INSURANCE = "INSURANCE"
    TAX = "TAX"
    DONATION = "DONATION"
    OTHER = "OTHER"

class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    DELIVERED = "DELIVERED"

class ProjectCreate(BaseModel):
    project_name: str
    client_id: int
    case_number: Optional[str] = None
    appraisal_type: AppraisalType = AppraisalType.DIVORCE  # Default to divorce
    purpose: Optional[str] = None
    inspection_date: Optional[date] = None
    report_date: Optional[date] = None
    assigned_user_id: Optional[int] = None
    notes: Optional[str] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    client_id: Optional[int] = None
    case_number: Optional[str] = None
    appraisal_type: Optional[AppraisalType] = None
    purpose: Optional[str] = None
    inspection_date: Optional[date] = None
    report_date: Optional[date] = None
    assigned_user_id: Optional[int] = None
    status: Optional[ProjectStatus] = None
    dropbox_folder_link: Optional[str] = None
    notes: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    project_name: str
    client_id: int
    client_name: str  # From joined client table
    case_number: Optional[str] = None
    appraisal_type: str
    purpose: Optional[str] = None
    inspection_date: Optional[date] = None
    report_date: Optional[date] = None
    assigned_user_id: Optional[int] = None
    assigned_user_name: Optional[str] = None  # From joined user table
    status: str
    dropbox_folder_link: Optional[str] = None
    total_value: Optional[float] = 0
    item_count: int = 0
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True