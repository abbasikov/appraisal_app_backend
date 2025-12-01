from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Date, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class AppraisalType(enum.Enum):
    DIVORCE = "DIVORCE"
    ESTATE = "ESTATE"
    INSURANCE = "INSURANCE"
    TAX = "TAX"
    DONATION = "DONATION"
    OTHER = "OTHER"

class ProjectStatus(enum.Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    DELIVERED = "DELIVERED"

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    case_number = Column(String)
    appraisal_type = Column(Enum(AppraisalType), nullable=False)
    purpose = Column(Text)
    inspection_date = Column(Date)
    report_date = Column(Date)
    effective_date = Column(Date)  # Effective date for the appraisal
    appraisal_location = Column(String)  # Location where appraisal takes place
    estate_of = Column(String)  # Name of the estate (for ESTATE appraisals)
    date_of_death = Column(Date)  # Date of death (for ESTATE appraisals)
    dropbox_folder_link = Column(String)
    dropbox_folder_id = Column(String)
    notification_email = Column(String)  # Email for import notifications
    address_letter_to = Column(String)  # person to send letter to
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    total_value = Column(Numeric(12, 2), default=0.00)
    item_count = Column(Integer, default=0)
    template_id = Column(Integer, ForeignKey("templates.id"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="projects")
    account = relationship("Account", back_populates="projects")
    assigned_user = relationship("User")
    template = relationship("Template")
    photos = relationship("Photo", back_populates="project")
    items = relationship("Item", back_populates="project")
    appraisal_items = relationship("AppraisalItem", back_populates="project")
    reports = relationship("Report", back_populates="project")
    activity_logs = relationship("ActivityLog", back_populates="project")
    task_statuses = relationship("TaskStatus", back_populates="project")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.project_name}', status='{self.status.value}')>"