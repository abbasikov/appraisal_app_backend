from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class TaskStatus(Base):
    __tablename__ = "task_status"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, nullable=False, index=True)
    task_type = Column(String, nullable=False)  # e.g., 'photo_import'
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    progress = Column(Integer, default=0)  # 0-100 percentage
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    error_message = Column(Text)
    result_data = Column(Text)  # JSON string of task results
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    project = relationship("Project", back_populates="task_statuses")
    user = relationship("User", back_populates="task_statuses")
    
    def __repr__(self):
        return f"<TaskStatus(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"
