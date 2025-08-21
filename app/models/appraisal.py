from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class AppraisalType(enum.Enum):
    PURCHASE = "purchase"
    REFINANCE = "refinance"
    TAX_ASSESSMENT = "tax_assessment"

class AppraisalStatus(enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"

class Appraisal(Base):
    __tablename__ = "appraisals"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    appraiser_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appraisal_type = Column(Enum(AppraisalType), nullable=False)
    purpose = Column(String)
    effective_date = Column(Date)
    status = Column(Enum(AppraisalStatus), default=AppraisalStatus.DRAFT)
    final_value = Column(Float)
    cost_approach = Column(Float)
    sales_approach = Column(Float)
    income_approach = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property")
    appraiser = relationship("User", foreign_keys=[appraiser_id])
    client = relationship("User", foreign_keys=[client_id])