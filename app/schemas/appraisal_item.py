from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AppraisalItemBase(BaseModel):
    photo_id: Optional[int] = None
    line_number: int
    room_area: Optional[str] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    appraised_value: Optional[float] = None
    sort_order: int = 0

class AppraisalItemCreate(AppraisalItemBase):
    project_id: int

class AppraisalItemUpdate(BaseModel):
    room_area: Optional[str] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    appraised_value: Optional[float] = None
    sort_order: Optional[int] = None

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