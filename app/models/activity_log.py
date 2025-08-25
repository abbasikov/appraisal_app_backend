from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INET
from app.db.database import Base

class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    action = Column(String, nullable=False)
    details = Column(JSON)  # Store action details as JSON
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    project = relationship("Project", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"