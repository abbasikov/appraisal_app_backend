from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric, JSON
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
    floor_building = Column(String)
    item_type = Column(String)
    description = Column(Text)
    appraised_value = Column(Numeric(12, 2), default=0.00)
    photos = Column(JSON, default=list)  # List of photo IDs/paths
    attributes = Column(JSON, default=dict)  # Type-specific attributes
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="appraisal_items")
    photo = relationship("Photo")

    def __repr__(self):
        return f"<AppraisalItem(id={self.id}, type='{self.item_type}', line_number={self.line_number}, project_id={self.project_id})>"
    
    def validate_attributes(self):
        """
        Validate attributes against JSON schema for item_type
        Returns (is_valid, error_message)
        """
        from app.schemas.appraisal_schemas import validate_appraisal_attributes
        if self.attributes and self.item_type:
            return validate_appraisal_attributes(self.item_type, self.attributes)
        return True, ""