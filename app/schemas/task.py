from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskStatusResponse(BaseModel):
    id: int
    task_id: str
    task_type: str
    project_id: int
    user_id: int
    status: TaskStatusEnum
    progress: int
    total_items: int
    processed_items: int
    error_message: Optional[str] = None
    result_data: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BackgroundPhotoImportRequest(BaseModel):
    recurring: bool = False  # If True, continue processing all batches until complete
    # Note: batch_size is determined automatically by the backend based on server load and file sizes

class BackgroundPhotoImportResponse(BaseModel):
    task_id: str
    message: str
    project_id: int
    recurring: bool
    estimated_duration: Optional[str] = None
    auto_batching_info: Optional[str] = None  # Information about automatic batching strategy
