from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.appraisal_constants import ROOM_AREA_OPTIONS, FLOOR_BUILDING_OPTIONS, ITEM_TYPE_OPTIONS, TYPE_ATTRIBUTES, REQUIRED_ATTRIBUTES

class AppraisalItemBase(BaseModel):
    photo_id: Optional[int] = None
    line_number: int
    room_area: Optional[str] = None
    floor_building: Optional[str] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    appraised_value: Optional[float] = None
    photos: List[str] = []
    attributes: Dict[str, Any] = {}
    sort_order: int = 0
    
    @validator('room_area')
    def validate_room_area(cls, v):
        if v and v not in ROOM_AREA_OPTIONS:
            raise ValueError(f'Invalid room_area. Must be one of: {ROOM_AREA_OPTIONS}')
        return v
    
    @validator('floor_building')
    def validate_floor_building(cls, v):
        if v and v not in FLOOR_BUILDING_OPTIONS:
            raise ValueError(f'Invalid floor_building. Must be one of: {FLOOR_BUILDING_OPTIONS}')
        return v
    
    @validator('item_type')
    def validate_item_type(cls, v):
        if v and v not in ITEM_TYPE_OPTIONS:
            raise ValueError(f'Invalid item_type. Must be one of: {ITEM_TYPE_OPTIONS}')
        return v

class AppraisalItemCreate(AppraisalItemBase):
    project_id: int
    
    @validator('attributes')
    def validate_attributes(cls, v, values):
        item_type = values.get('item_type')
        if item_type and item_type in REQUIRED_ATTRIBUTES:
            required_fields = REQUIRED_ATTRIBUTES[item_type]
            for field in required_fields:
                if field not in v or not v[field]:
                    raise ValueError(f'Required attribute {field} missing for type {item_type}')
        return v

class AppraisalItemUpdate(BaseModel):
    room_area: Optional[str] = None
    floor_building: Optional[str] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    appraised_value: Optional[float] = None
    photos: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = None
    
    @validator('room_area')
    def validate_room_area(cls, v):
        if v and v not in ROOM_AREA_OPTIONS:
            raise ValueError(f'Invalid room_area. Must be one of: {ROOM_AREA_OPTIONS}')
        return v
    
    @validator('floor_building')
    def validate_floor_building(cls, v):
        if v and v not in FLOOR_BUILDING_OPTIONS:
            raise ValueError(f'Invalid floor_building. Must be one of: {FLOOR_BUILDING_OPTIONS}')
        return v
    
    @validator('item_type')
    def validate_item_type(cls, v):
        if v and v not in ITEM_TYPE_OPTIONS:
            raise ValueError(f'Invalid item_type. Must be one of: {ITEM_TYPE_OPTIONS}')
        return v

class AppraisalItemResponse(AppraisalItemBase):
    id: int
    project_id: int
    photo_thumbnail: Optional[str] = None
    photo_filename: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AppraisalItemReorder(BaseModel):
    item_id: int
    new_sort_order: int

class AppraisalSchemaResponse(BaseModel):
    room_area_options: List[str]
    floor_building_options: List[str]
    item_type_options: List[str]
    type_attributes: Dict[str, List[str]]
    required_attributes: Dict[str, List[str]]
    description_templates: Optional[Dict[str, str]] = {}