from pydantic import BaseModel, computed_field
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
    
    # Computed field for template category (detected from name)
    @computed_field
    @property
    def template_category(self) -> str:
        """Detect template category from name"""
        from app.utils.template_detector import detect_template_category
        return detect_template_category(self.name).value
    
    # Computed field for column configuration
    @computed_field
    @property
    def column_config(self) -> dict:
        """Get column configuration for this template"""
        from app.utils.template_detector import detect_template_category, get_template_columns
        category = detect_template_category(self.name)
        return get_template_columns(category)
    
    class Config:
        from_attributes = True

class FieldMappingUpdate(BaseModel):
    field_mappings: Dict

class ReportGenerationRequest(BaseModel):
    project_id: int
    report_type: str = "final"
    include_photos: bool = True

class TemplateListResponse(BaseModel):
    templates: List[TemplateResponse]
    total: int