from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class ReportType(enum.Enum):
    URAR = "urar"
    COMMERCIAL = "commercial"
    NARRATIVE = "narrative"

class ReportStatus(enum.Enum):
    DRAFT = "draft"
    FINAL = "final"
    DELIVERED = "delivered"

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    appraisal_id = Column(Integer, ForeignKey("appraisals.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("form_templates.id"))
    report_type = Column(Enum(ReportType), nullable=False)
    file_path = Column(String)
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    appraisal = relationship("Appraisal")
    template = relationship("FormTemplate")