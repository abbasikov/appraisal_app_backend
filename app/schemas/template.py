from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class TemplateCreate(BaseModel):
    name: str
    appraisal_type: str
    description: Optional[str] = None

class TemplateResponse(BaseModel):
    id: int
    name: str
    appraisal_type: str
    description: Optional[str]
    field_mappings: Optional[Dict]
    is_active: bool
    version: str
    created_at: datetime
    created_by: Optional[int]
    
    class Config:
        from_attributes = True

class FieldMappingUpdate(BaseModel):
    field_mappings: Dict

class ReportGenerationRequest(BaseModel):
    project_id: int
    report_type: str = "draft"
    include_photos: bool = True

class TemplateListResponse(BaseModel):
    templates: List[TemplateResponse]
    total: int