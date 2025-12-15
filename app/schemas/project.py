from pydantic import BaseModel, model_validator
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
    case_name: Optional[str] = None  # Case name to store in client table
    case_number: Optional[str] = None
    appraisal_type: AppraisalType  # No default - must be selected
    purpose: Optional[str] = None
    inspection_date: Optional[date] = None
    report_date: Optional[date] = None
    effective_date: Optional[date] = None
    appraisal_location: Optional[str] = None
    estate_of: Optional[str] = None  # Name of the estate (for ESTATE appraisals)
    date_of_death: Optional[date] = None  # Date of death (for ESTATE appraisals)
    address_letter_to: str  # REQUIRED: person to send letter to
    assigned_user_id: Optional[int] = None
    account_id: Optional[int] = None  # Account/Law firm associated with project
    template_id: Optional[int] = None
    notes: Optional[str] = None

    @model_validator(mode='after')
    def validate_conditional_fields(self) -> 'ProjectCreate':
        # 1. case_name required for DIVORCE
        if self.appraisal_type == AppraisalType.DIVORCE and not self.case_name:
            raise ValueError('Case Name is required for Divorce appraisals')
        
        # 2. estate_of required for ESTATE
        if self.appraisal_type == AppraisalType.ESTATE and not self.estate_of:
            raise ValueError('Estate Of is required for Estate appraisals')
            
        # 3. effective_date required for DIVORCE
        if self.appraisal_type == AppraisalType.DIVORCE and not self.effective_date:
            raise ValueError('Effective Date is required for Divorce appraisals')
            
        # 4. appointment_date (inspection_date) required for ALL
        if not self.inspection_date:
            raise ValueError('Inspection Date is required')
            
        return self

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    client_id: Optional[int] = None
    case_number: Optional[str] = None
    appraisal_type: Optional[AppraisalType] = None
    purpose: Optional[str] = None
    inspection_date: Optional[date] = None
    report_date: Optional[date] = None
    effective_date: Optional[date] = None
    appraisal_location: Optional[str] = None
    estate_of: Optional[str] = None  # Name of the estate (for ESTATE appraisals)
    date_of_death: Optional[date] = None  # Date of death (for ESTATE appraisals)
    address_letter_to: Optional[str] = None  # Person to send letter to
    assigned_user_id: Optional[int] = None
    account_id: Optional[int] = None  # Account/Law firm associated with project
    template_id: Optional[int] = None
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
    effective_date: Optional[date] = None
    appraisal_location: Optional[str] = None
    estate_of: Optional[str] = None  # Name of the estate (for ESTATE appraisals)
    date_of_death: Optional[date] = None  # Date of death (for ESTATE appraisals)
    address_letter_to: Optional[str] = None  # Person to send letter to
    assigned_user_id: Optional[int] = None
    assigned_user_name: Optional[str] = None  # From joined user table
    status: str
    dropbox_folder_link: Optional[str] = None
    dropbox_links: List[str] = []
    template_id: Optional[int] = None
    total_value: Optional[float] = 0
    item_count: int = 0
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True