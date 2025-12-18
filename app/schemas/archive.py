from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArchiveCreate(BaseModel):
    client_id: int
    account_id: int
    archive_status: bool = True


class ArchiveUpdate(BaseModel):
    archive_status: bool


class ArchiveResponse(BaseModel):
    id: int
    client_id: int
    account_id: int
    archive_status: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
