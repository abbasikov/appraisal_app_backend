from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class ReportType(enum.Enum):
    DRAFT = "draft"
    FINAL = "final"

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"))
    template_name = Column(String, nullable=False)
    report_type = Column(Enum(ReportType), default=ReportType.DRAFT)
    file_path = Column(String)
    pdf_path = Column(String)
    word_path = Column(String)
    has_watermark = Column(Boolean, default=True)
    generated_at = Column(DateTime(timezone=True))
    dropbox_file_id = Column(String)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="reports")
    template = relationship("Template", back_populates="reports")

    def __repr__(self):
        return f"<Report(id={self.id}, project_id={self.project_id}, type='{self.report_type.value}')>"