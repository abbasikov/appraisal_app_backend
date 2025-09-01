from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PhotoResponse(BaseModel):
    id: int
    project_id: int
    original_filename: str
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    exif_date: Optional[datetime]
    sort_order: int
    dropbox_folder_path: Optional[str] = None
    source_folder_link: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class DropboxLinksRequest(BaseModel):
    links: list[str]