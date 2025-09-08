from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class AppraisalItem(Base):
    __tablename__ = "appraisal_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=True)
    line_number = Column(Integer, nullable=False)
    room_area = Column(String)
    item_type = Column(String)
    description = Column(Text)
    appraised_value = Column(Numeric(12, 2), default=0.00)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="appraisal_items")
    photo = relationship("Photo")

    def __repr__(self):
        return f"<AppraisalItem(id={self.id}, line_number={self.line_number}, project_id={self.project_id})>"