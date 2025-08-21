from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class PhotoType(enum.Enum):
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    COMPARABLE = "comparable"

class PropertyPhoto(Base):
    __tablename__ = "property_photos"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    appraisal_id = Column(Integer, ForeignKey("appraisals.id"))
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    photo_type = Column(Enum(PhotoType), nullable=False)
    description = Column(String)
    sequence_order = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    property = relationship("Property")
    appraisal = relationship("Appraisal")