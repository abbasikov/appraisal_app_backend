from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    appraisal_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    description = Column(Text)
    field_mappings = Column(JSON)  # Store dynamic field mappings as JSON
    is_active = Column(Boolean, default=True)
    version = Column(String, default="1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    projects = relationship("Project", back_populates="template")
    reports = relationship("Report", back_populates="template")

    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}', type='{self.appraisal_type}')>"